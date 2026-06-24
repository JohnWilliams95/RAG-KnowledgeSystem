from __future__ import annotations

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from src.config import settings
from src.config.constants import IngestionStatus
from src.data_loader.loader_registry import loader_registry
from src.splitting.splitter_factory import SplitterFactory
from src.ingestion.document_store import DocumentStore
from src.ingestion.metadata_store import MetadataStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        document_store: DocumentStore,
        metadata_store: MetadataStore,
        *,
        skip_processed: bool = True,
        max_workers: Optional[int] = None,
    ):
        self._document_store = document_store
        self._metadata_store = metadata_store
        self._skip_processed = skip_processed
        self._max_workers = max_workers or settings.max_workers

    def ingest_file(self, file_path: str | Path, *, metadata: Optional[dict] = None) -> dict:
        file_path = Path(file_path)
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}

        if not loader_registry.is_supported(file_path):
            return {"status": "error", "message": f"Unsupported file type: {file_path.suffix}"}

        file_hash = MetadataStore._compute_file_hash(file_path)
        if self._skip_processed and self._metadata_store.is_file_processed(file_path, file_hash):
            return {"status": "skipped", "message": f"Already processed: {file_path.name}"}

        doc_id = self._metadata_store.register_document(
            file_path,
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
            file_hash=file_hash,
            metadata=metadata,
        )

        try:
            self._metadata_store.update_document_status(doc_id, IngestionStatus.PROCESSING)

            loader = loader_registry.create_loader(file_path, metadata=metadata)
            if loader is None:
                self._metadata_store.update_document_status(
                    doc_id, IngestionStatus.FAILED, error_message="No loader available"
                )
                return {"status": "error", "message": "No loader available"}

            documents = loader.load()
            logger.info(f"Loaded {len(documents)} document(s) from {file_path.name}")

            chunks = SplitterFactory.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")

            point_ids = self._document_store.add_documents(chunks)

            for i, chunk in enumerate(chunks):
                content_hash = hashlib.sha256(chunk.page_content.encode()).hexdigest()
                self._metadata_store.register_chunk(
                    doc_id, i, content_hash,
                    qdrant_point_id=point_ids[i] if i < len(point_ids) else None,
                    metadata=chunk.metadata,
                )

            self._metadata_store.update_document_status(
                doc_id, IngestionStatus.COMPLETED, chunk_count=len(chunks)
            )

            return {
                "status": "success",
                "doc_id": doc_id,
                "documents_loaded": len(documents),
                "chunks_created": len(chunks),
                "point_ids": point_ids,
            }

        except Exception as e:
            logger.error(f"Ingestion failed for {file_path.name}: {e}", exc_info=True)
            self._metadata_store.update_document_status(
                doc_id, IngestionStatus.FAILED, error_message=str(e)
            )
            return {"status": "error", "message": str(e)}

    def ingest_directory(
        self,
        directory: str | Path,
        *,
        recursive: bool = True,
        metadata: Optional[dict] = None,
    ) -> dict:
        directory = Path(directory)
        if not directory.is_dir():
            return {"status": "error", "message": f"Not a directory: {directory}"}

        files = self._scan_directory(directory, recursive=recursive)
        if not files:
            return {"status": "error", "message": "No supported files found"}

        logger.info(f"Found {len(files)} supported files in {directory}")

        results: list[dict] = []
        total_chunks = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self.ingest_file, f, metadata=metadata): f
                for f in files
            }

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    results.append({"file": str(file_path), **result})
                    if result.get("status") == "success":
                        total_chunks += result.get("chunks_created", 0)
                    elif result.get("status") == "error":
                        errors += 1
                except Exception as e:
                    errors += 1
                    results.append({"file": str(file_path), "status": "error", "message": str(e)})

        return {
            "status": "completed",
            "total_files": len(files),
            "total_chunks": total_chunks,
            "errors": errors,
            "results": results,
        }

    def _scan_directory(self, directory: Path, *, recursive: bool = True) -> list[Path]:
        from src.config.constants import SUPPORTED_EXTENSIONS

        files: list[Path] = []
        if recursive:
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(directory.glob(f"*{ext}"))

        return sorted(set(files))

    def remove_file(self, file_path: str | Path) -> dict:
        file_path = Path(file_path)
        doc = self._metadata_store.get_document_by_path(file_path)
        if not doc:
            return {"status": "error", "message": f"Document not found: {file_path}"}

        try:
            point_ids = self._get_point_ids_for_doc(doc["doc_id"])
            if point_ids:
                self._document_store.delete_documents(point_ids)
            self._metadata_store.delete_document(doc["doc_id"])
            return {"status": "success", "deleted_points": len(point_ids)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_point_ids_for_doc(self, doc_id: str) -> list[str]:
        conn = self._metadata_store._get_conn()
        rows = conn.execute(
            "SELECT qdrant_point_id FROM chunks WHERE doc_id = ? AND qdrant_point_id IS NOT NULL",
            (doc_id,),
        ).fetchall()
        return [row["qdrant_point_id"] for row in rows]