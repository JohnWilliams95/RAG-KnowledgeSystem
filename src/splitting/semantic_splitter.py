from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.documents import Document

from src.config import settings

logger = logging.getLogger(__name__)


class BaseSplitter(ABC):
    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        ...

    def _merge_metadata(self, parent_meta: dict, chunk_index: int) -> dict:
        meta = dict(parent_meta)
        meta["chunk_index"] = chunk_index
        return meta


class SemanticSplitter(BaseSplitter):
    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-m3",
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        similarity_threshold: float = 0.5,
        buffer_size: int = 1,
        device: str = "cpu",
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._similarity_threshold = similarity_threshold
        self._buffer_size = buffer_size
        self._model_name = model_name
        self._device = device
        self._embedder = None

    def _init_embedder(self):
        if self._embedder is not None:
            return
        from FlagEmbedding import FlagModel

        self._embedder = FlagModel(
            self._model_name,
            query_instruction_for_retrieval="",
            use_fp16=(self._device != "cpu"),
            devices=self._device,
        )
        logger.info(f"Semantic splitter embedder loaded: {self._model_name}")

    def split(self, documents: list[Document]) -> list[Document]:
        self._init_embedder()
        result: list[Document] = []

        for doc in documents:
            chunks = self._split_document(doc)
            result.extend(chunks)

        return result

    def _split_document(self, doc: Document) -> list[Document]:
        text = doc.page_content
        if not text.strip():
            return [doc]

        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [doc]

        if len(text) <= self._chunk_size:
            return [doc]

        embeddings = self._embedder.encode(sentences)["dense_embeds"]
        import numpy as np

        embeddings = np.array(embeddings)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normed = embeddings / norms

        split_points = self._detect_boundaries(normed)

        chunks = self._merge_sentences(sentences, split_points, doc)
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        import re

        pattern = r"(?<=[。！？.!?\n])\s*"
        parts = re.split(pattern, text)
        return [p.strip() for p in parts if p.strip()]

    def _detect_boundaries(self, normed_embeddings) -> list[int]:
        import numpy as np

        split_points: list[int] = []
        for i in range(len(normed_embeddings) - 1):
            sim = float(np.dot(normed_embeddings[i], normed_embeddings[i + 1]))
            if sim < self._similarity_threshold:
                split_points.append(i + 1)
        return split_points

    def _merge_sentences(
        self,
        sentences: list[str],
        split_points: list[int],
        doc: Document,
    ) -> list[Document]:
        boundaries = [0] + split_points + [len(sentences)]
        chunks: list[Document] = []

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_text = " ".join(sentences[start:end])

            if len(chunk_text) > self._chunk_size * 2:
                sub_chunks = self._fixed_size_split(chunk_text)
                for j, sub in enumerate(sub_chunks):
                    meta = self._merge_metadata(doc.metadata, len(chunks))
                    meta["split_method"] = "semantic_then_fixed"
                    chunks.append(Document(page_content=sub, metadata=meta))
            else:
                meta = self._merge_metadata(doc.metadata, len(chunks))
                meta["split_method"] = "semantic"
                chunks.append(Document(page_content=chunk_text, metadata=meta))

        return chunks

    def _fixed_size_split(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            start = end - self._chunk_overlap
        return chunks


class RecursiveSplitter(BaseSplitter):
    DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]

    def __init__(
        self,
        *,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or self.DEFAULT_SEPARATORS

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=self._separators,
            length_function=len,
            is_separator_regex=False,
        )

        chunks: list[Document] = []
        for doc in documents:
            split_docs = splitter.split_documents([doc])
            for i, chunk in enumerate(split_docs):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["split_method"] = "recursive"
                chunks.append(chunk)

        return chunks


class CodeSplitter(BaseSplitter):
    LANGUAGE_MAP = {
        "python": "python",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "go": "go",
        "rust": "rust",
        "cpp": "cpp",
        "c": "c",
    }

    def __init__(
        self,
        *,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import (
            Language,
            RecursiveCharacterTextSplitter,
        )

        chunks: list[Document] = []
        for doc in documents:
            language_str = doc.metadata.get("language", "python")
            lang_enum = self._resolve_language(language_str)

            if lang_enum:
                splitter = RecursiveCharacterTextSplitter.from_language(
                    language=lang_enum,
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )

            split_docs = splitter.split_documents([doc])
            for i, chunk in enumerate(split_docs):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["split_method"] = "code_aware"
                chunks.append(chunk)

        return chunks

    def _resolve_language(self, language_str: str):
        from langchain_text_splitters import Language

        lookup = {
            "python": Language.PYTHON,
            "javascript": Language.JS,
            "js": Language.JS,
            "typescript": Language.TS,
            "ts": Language.TS,
            "java": Language.JAVA,
            "go": Language.GO,
            "rust": Language.RUST,
            "cpp": Language.CPP,
            "c": Language.C,
        }
        return lookup.get(language_str.lower())
