from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile

from src.api.schemas.request import (
    DeleteDocumentRequest,
    IngestDirectoryRequest,
    IngestFileRequest,
)
from src.api.schemas.response import IngestResponse, IngestDirectoryResponse
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
    logger.info(f"[Upload] Received file: {file.filename}")
    
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or f"upload_{uuid.uuid4().hex[:8]}"
    # 使用 UUID 前缀避免文件名冲突
    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = upload_dir / safe_name

    content = await file.read()
    save_path.write_bytes(content)
    logger.info(f"[Upload] Saved to: {save_path} ({len(content)} bytes)")

    try:
        result = pipeline.ingest_file(str(save_path))
        logger.info(f"[Upload] Ingestion result: {result}")
    except Exception as e:
        logger.error(f"[Upload] Ingestion error: {e}", exc_info=True)
        # 清理失败的上传文件
        if save_path.exists():
            save_path.unlink()
        result = {"status": "error", "message": str(e)}
    
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
        # 同时删除上传目录中的源文件
        _delete_upload_file(request.file_path)
    elif request.doc_id:
        # 获取文档信息，用于后续删除源文件
        doc_info = pipeline._metadata_store.get_document(request.doc_id)
        file_path = doc_info.get("file_path") if doc_info else None
        
        # 先删除 Qdrant 中的向量数据
        try:
            point_ids = pipeline._get_point_ids_for_doc(request.doc_id)
            if point_ids:
                pipeline._document_store.delete_documents(point_ids)
                logger.info(f"Deleted {len(point_ids)} points from Qdrant for doc {request.doc_id}")
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant points for doc {request.doc_id}: {e}")
        
        # 再删除 SQLite 元数据
        pipeline._metadata_store.delete_document(request.doc_id)
        
        # 删除上传目录中的源文件
        if file_path:
            _delete_upload_file(file_path)
        
        result = {"status": "success", "message": f"Document {request.doc_id} deleted"}
    else:
        return {"status": "error", "message": "Provide file_path or doc_id"}

    return result


def _delete_upload_file(file_path: str) -> None:
    """删除上传目录中的源文件"""
    try:
        path = Path(file_path)
        # 只删除 data/uploads/ 目录下的文件
        if path.exists() and "uploads" in str(path):
            path.unlink()
            logger.info(f"Deleted upload file: {path}")
    except Exception as e:
        logger.warning(f"Failed to delete upload file {file_path}: {e}")