from __future__ import annotations

from langchain_core.documents import Document

from backend.src.splitting.base_splitter import BaseSplitter


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
