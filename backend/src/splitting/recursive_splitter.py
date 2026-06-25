from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document

from backend.src.splitting.base_splitter import BaseSplitter


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
