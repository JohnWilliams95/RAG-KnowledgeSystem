from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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


class DocumentInfoResponse(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    conversation_id: str
    rewritten_queries: list[str] = Field(default_factory=list)
    num_documents: int = 0
    context_length: int = 0
    metadata: dict = Field(default_factory=dict)


class ChatStreamEvent(BaseModel):
    event_type: str
    data: str
    metadata: Optional[dict] = None


class RetrievedDocument(BaseModel):
    page_content: str
    metadata: dict = Field(default_factory=dict)
    score: Optional[float] = None
    rerank_score: Optional[float] = None


class RetrievalResponse(BaseModel):
    query: str
    documents: list[RetrievedDocument] = Field(default_factory=list)
    total: int = 0


class KnowledgeBaseInfo(BaseModel):
    collection_name: str
    exists: bool
    points_count: Optional[int] = None
    vectors_count: Optional[int] = None
    status: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    qdrant_connected: bool
    collection_info: Optional[KnowledgeBaseInfo] = None