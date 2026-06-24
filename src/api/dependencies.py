from __future__ import annotations

from functools import lru_cache
from typing import Optional

from langchain_core.language_models import BaseChatModel

from src.config import settings
from src.embedding.bge_embedding import BGEM3Embedding
from src.ingestion.document_store import DocumentStore
from src.ingestion.metadata_store import MetadataStore
from src.memory.conversation_memory import ConversationMemory
from src.retrieval.ensemble_retriever import EnsembleRetriever


@lru_cache()
def get_llm() -> BaseChatModel:
    from langchain.chat_models import init_chat_model
    return init_chat_model(
        settings.llm_model,
        model_provider=settings.llm_provider,
        **settings.llm_init_kwargs,
    )


@lru_cache()
def get_embedding_model() -> BGEM3Embedding:
    return BGEM3Embedding()


@lru_cache()
def get_document_store() -> DocumentStore:
    return DocumentStore(
        embedding_model=get_embedding_model(),
    )


@lru_cache()
def get_metadata_store() -> MetadataStore:
    return MetadataStore()


@lru_cache()
def get_ensemble_retriever() -> EnsembleRetriever:
    return EnsembleRetriever(
        document_store=get_document_store(),
        embedding_model=get_embedding_model(),
    )


@lru_cache()
def get_memory() -> ConversationMemory:
    return ConversationMemory()