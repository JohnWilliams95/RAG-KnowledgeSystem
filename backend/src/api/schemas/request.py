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


class DeleteDocumentRequest(BaseModel):
    file_path: Optional[str] = None
    doc_id: Optional[str] = None


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


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="检索查询")
    top_k: Optional[int] = Field(default=None, description="检索数量")
    rerank_top_n: Optional[int] = Field(default=None, description="重排序数量")
    rerank_enabled: bool = Field(default=True, description="启用重排序")
    method: str = Field(default="rrf", description="融合方法: rrf/weighted")