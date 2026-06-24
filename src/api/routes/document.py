from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile

from src.api.schemas.request import (
    DeleteDocumentRequest,
    IngestDirectoryRequest,
    IngestFileRequest,
)
from src.api.schemas.response import IngestDirectoryResponse, IngestResponse
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.document_store import DocumentStore
from src.ingestion.metadata_store import MetadataStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_pipeline: Optional[IngestionPipeline] = None


def get_pipeline() -> IngestionPipeline:
    global _pipeline
    if _pipeline is None:
        from src.api.dependencies import get_document_store, get_metadata_store
        ds = get_document_store()
        ms = get_metadata_store()
        _pipeline = IngestionPipeline(ds, ms)
    return _pipeline


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    request: IngestFileRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    result = pipeline.ingest_file(request.file_path, metadata=request.metadata)
    return IngestResponse(
        status=result.get("status", "unknown"),
        doc_id=result.get("doc_id"),
        documents_loaded=result.get("documents_loaded", 0),
        chunks_created=result.get("chunks_created", 0),
        point_ids=result.get("point_ids"),
        message=result.get("message"),
    )


@router.post("/ingest/directory", response_model=IngestDirectoryResponse)
async def ingest_directory(
    request: IngestDirectoryRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    result = pipeline.ingest_directory(
        request.directory,
        recursive=request.recursive,
        metadata=request.metadata,
    )
    return IngestDirectoryResponse(
        status=result.get("status", "unknown"),
        total_files=result.get("total_files", 0),
        total_chunks=result.get("total_chunks", 0),
        errors=result.get("errors", 0),
        results=result.get("results"),
    )


@router.post("/ingest/upload")
async def upload_file(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / file.filename

    content = await file.read()
    save_path.write_bytes(content)

    result = pipeline.ingest_file(str(save_path))
    return IngestResponse(
        status=result.get("status", "unknown"),
        doc_id=result.get("doc_id"),
        documents_loaded=result.get("documents_loaded", 0),
        chunks_created=result.get("chunks_created", 0),
        message=result.get("message"),
    )


@router.delete("/")
async def delete_document(
    request: DeleteDocumentRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    if request.file_path:
        result = pipeline.remove_file(request.file_path)
    elif request.doc_id:
        result = pipeline._metadata_store.delete_document(request.doc_id)
        result = {"status": "success", "message": f"Document {request.doc_id} deleted"}
    else:
        return {"status": "error", "message": "Provide file_path or doc_id"}

    return result