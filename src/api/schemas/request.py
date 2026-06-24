from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IngestFileRequest(BaseModel):
    file_path: str = Field(..., description="文件路径")
    metadata: Optional[dict] = Field(default=None, description="附加元数据")
    skip_processed: bool = Field(default=True, description="跳过已处理文件")


class IngestDirectoryRequest(BaseModel):
    directory: str = Field(..., description="目录路径")
    recursive: bool = Field(default=True, description="递归扫描子目录")
    metadata: Optional[dict] = Field(default=None, description="附加元数据")


class IngestResponse(BaseModel):
    status: str
    doc_id: Optional[str] = None
    documents_loaded: int = 0
    chunks_created: int = 0
    point_ids: Optional[list[str]] = None
    message: Optional[str] = None


class IngestDirectoryResponse(BaseModel):
    status: str
    total_files: int = 0
    total_chunks: int = 0
    errors: int = 0
    results: Optional[list[dict]] = None


class DeleteDocumentRequest(BaseModel):
    file_path: Optional[str] = None
    doc_id: Optional[str] = None


class DocumentInfoResponse(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: str
