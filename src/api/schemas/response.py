from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000, description="用户问题")
    conversation_id: Optional[str] = Field(default=None, description="对话ID")
    enable_query_rewriting: bool = Field(default=True, description="启用查询重写")
    enable_reranking: bool = Field(default=True, description="启用重排序")
    enable_hyde: bool = Field(default=True, description="启用HyDE")
    enable_stepback: bool = Field(default=False, description="启用Step-Back")
    enable_decomposition: bool = Field(default=False, description="启用问题分解")
    prompt_style: str = Field(default="detailed", description="提示风格: concise/detailed/academic")
    top_k: Optional[int] = Field(default=None, description="检索top-k")
    rerank_top_n: Optional[int] = Field(default=None, description="重排序top-n")


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


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="检索查询")
    top_k: Optional[int] = Field(default=None, description="检索数量")
    rerank_top_n: Optional[int] = Field(default=None, description="重排序数量")
    rerank_enabled: bool = Field(default=True, description="启用重排序")
    method: str = Field(default="rrf", description="融合方法: rrf/weighted")


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