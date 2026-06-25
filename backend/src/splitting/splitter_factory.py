from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document

from src.config import settings
from backend.src.config.constants import CODE_EXTENSIONS
from backend.src.splitting.base_splitter import BaseSplitter
from backend.src.splitting.semantic_splitter import SemanticSplitter
from backend.src.splitting.recursive_splitter import RecursiveSplitter
from backend.src.splitting.code_splitter import CodeSplitter
from backend.src.splitting.heading_splitter import HeadingSplitter
from backend.src.splitting.paragraph_splitter import ParagraphSplitter


class SplitterFactory:
    @staticmethod
    def create(
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> BaseSplitter:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap
        se = semantic_enabled if semantic_enabled is not None else settings.semantic_chunking_enabled

        if se:
            return SemanticSplitter(
                chunk_size=cs,
                chunk_overlap=co,
                device=settings.embedding_device,
                model_name=settings.embedding_model_name,
            )
        return RecursiveSplitter(chunk_size=cs, chunk_overlap=co)

    @staticmethod
    def _classify_documents(
        documents: list[Document],
    ) -> tuple[list[Document], list[Document], list[Document]]:
        code_docs: list[Document] = []
        heading_docs: list[Document] = []
        regular_docs: list[Document] = []

        for doc in documents:
            lang = doc.metadata.get("language")
            ext = doc.metadata.get("file_type", "")
            if lang or ext in CODE_EXTENSIONS:
                code_docs.append(doc)
            elif ext in {".md", ".markdown", ".rst"}:
                heading_docs.append(doc)
            else:
                regular_docs.append(doc)

        return code_docs, heading_docs, regular_docs

    @staticmethod
    def create_for_documents(
        documents: list[Document],
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> list[BaseSplitter]:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap

        code_docs, heading_docs, regular_docs = SplitterFactory._classify_documents(documents)

        splitters: list[BaseSplitter] = []
        if code_docs:
            splitters.append(CodeSplitter(chunk_size=max(cs, 1500), chunk_overlap=co))
        if heading_docs:
            splitters.append(HeadingSplitter(chunk_size=cs, chunk_overlap=co))
        if regular_docs:
            splitters.append(SplitterFactory.create(
                chunk_size=cs,
                chunk_overlap=co,
                semantic_enabled=semantic_enabled,
            ))
        return splitters

    @staticmethod
    def split_documents(
        documents: list[Document],
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> list[Document]:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap

        code_docs, heading_docs, regular_docs = SplitterFactory._classify_documents(documents)

        all_chunks: list[Document] = []

        if code_docs:
            code_splitter = CodeSplitter(chunk_size=max(cs, 1500), chunk_overlap=co)
            all_chunks.extend(code_splitter.split(code_docs))

        if heading_docs:
            heading_splitter = HeadingSplitter(chunk_size=cs, chunk_overlap=co)
            all_chunks.extend(heading_splitter.split(heading_docs))

        if regular_docs:
            se = semantic_enabled if semantic_enabled is not None else settings.semantic_chunking_enabled
            regular_splitter = SplitterFactory.create(
                chunk_size=cs, chunk_overlap=co, semantic_enabled=se,
            )
            all_chunks.extend(regular_splitter.split(regular_docs))

        return all_chunks