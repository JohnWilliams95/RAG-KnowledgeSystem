from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(
        self,
        *,
        max_context_length: int = 8000,
        deduplicate: bool = True,
        add_metadata: bool = True,
        summarize_if_long: bool = True,
    ):
        self._max_context_length = max_context_length
        self._deduplicate = deduplicate
        self._add_metadata = add_metadata
        self._summarize_if_long = summarize_if_long
        self._llm = None

    def build(
        self,
        documents: list[Document],
        *,
        query: Optional[str] = None,
        style: str = "default",
    ) -> str:
        if not documents:
            return ""

        docs = self._deduplicate_docs(documents) if self._deduplicate else documents
        docs = self._filter_relevant(docs, query=query)
        docs = self._sort_by_relevance(docs)

        context_parts: list[str] = []
        total_length = 0

        for i, doc in enumerate(docs, start=1):
            part = self._format_document(doc, index=i)
            if total_length + len(part) > self._max_context_length:
                break
            context_parts.append(part)
            total_length += len(part)

        context = "\n\n---\n\n".join(context_parts)

        if self._summarize_if_long and len(context) > self._max_context_length * 0.8:
            context = self._truncate_with_overlap(context)

        return context

    def _deduplicate_docs(self, documents: list[Document]) -> list[Document]:
        seen: set[str] = set()
        unique: list[Document] = []
        for doc in documents:
            content_hash = hash(doc.page_content[:500])
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(doc)
        return unique

    def _filter_relevant(
        self,
        documents: list[Document],
        *,
        query: Optional[str] = None,
    ) -> list[Document]:
        filtered = []
        for doc in documents:
            rerank_score = doc.metadata.get("_rerank_score", 1.0)
            if rerank_score < 0.1:
                continue
            if not doc.page_content.strip():
                continue
            filtered.append(doc)
        return filtered

    def _sort_by_relevance(self, documents: list[Document]) -> list[Document]:
        def sort_key(doc: Document) -> float:
            rerank = doc.metadata.get("_rerank_score", 0.0)
            retrieval = doc.metadata.get("_score", 0.0)
            return max(rerank, retrieval)

        return sorted(documents, key=sort_key, reverse=True)

    def _format_document(self, doc: Document, *, index: int) -> str:
        parts: list[str] = []

        if self._add_metadata:
            source = doc.metadata.get("source_file", doc.metadata.get("source", ""))
            page = doc.metadata.get("page", "")
            chunk_index = doc.metadata.get("chunk_index", "")
            content_type = doc.metadata.get("content_type", "text")

            # 使用实际文件名作为标识
            if source:
                # 移除文件扩展名和UUID前缀，保留核心文件名
                display_name = source
                if "_" in display_name:
                    # 移除 UUID 前缀（如 "e2e64cab_回转窑..." 中的 "e2e64cab_"）
                    parts_split = display_name.split("_", 1)
                    if len(parts_split) > 1 and len(parts_split[0]) == 8:
                        display_name = parts_split[1]
                meta_parts = [f"[{display_name}]"]
            else:
                meta_parts = [f"[文档{index}]"]

            if page:
                meta_parts.append(f"页码: {page}")
            elif chunk_index != "":
                meta_parts.append(f"段落: {chunk_index + 1}")
            if content_type and content_type != "text":
                meta_parts.append(f"类型: {content_type}")

            parts.append(" | ".join(meta_parts))

        parts.append(doc.page_content)
        return "\n".join(parts)

    def _truncate_with_overlap(self, text: str) -> str:
        if len(text) <= self._max_context_length:
            return text
        return text[: self._max_context_length - 50] + "\n\n[...内容过长，已截断...]"