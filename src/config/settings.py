from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)

    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")

    embedding_model_name: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL_NAME")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    embedding_use_fp16: bool = Field(default=False, alias="EMBEDDING_USE_FP16")
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")
    embedding_cache_dir: str = Field(default="./cache/embeddings", alias="EMBEDDING_CACHE_DIR")

    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="rag_documents", alias="QDRANT_COLLECTION_NAME")
    qdrant_use_memory: bool = Field(default=False, alias="QDRANT_USE_MEMORY")

    chunk_size: int = Field(default=1024, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    semantic_chunking_enabled: bool = Field(default=True, alias="SEMANTIC_CHUNKING_ENABLED")
    max_workers: int = Field(default=4, alias="MAX_WORKERS")

    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    ocr_dpi: int = Field(default=300, alias="OCR_DPI")
    pdf_use_unstructured: bool = Field(default=False, alias="PDF_USE_UNSTRUCTURED")
    pdf_extract_images: bool = Field(default=True, alias="PDF_EXTRACT_IMAGES")

    retrieval_top_k: int = Field(default=20, alias="RETRIEVAL_TOP_K")
    rerank_top_n: int = Field(default=5, alias="RERANK_TOP_N")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")
    bm25_weight: float = Field(default=0.3, alias="BM25_WEIGHT")
    dense_weight: float = Field(default=0.7, alias="DENSE_WEIGHT")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_cors_origins: str = Field(default="*", alias="API_CORS_ORIGINS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="", alias="LANGFUSE_HOST")

    @property
    def llm_init_kwargs(self) -> dict:
        kwargs: dict = {}
        if self.llm_api_key:
            kwargs["api_key"] = self.llm_api_key
        if self.llm_base_url:
            kwargs["base_url"] = self.llm_base_url
        return kwargs

    def ensure_directories(self) -> None:
        os.makedirs(self.embedding_cache_dir, exist_ok=True)

    @classmethod
    def get_settings(cls) -> "Settings":
        return cls()


settings = Settings.get_settings()