from __future__ import annotations

from langchain_core.documents import Document

from src.splitting.base_splitter import BaseSplitter


class FixedSplitter(BaseSplitter):
    def __init__(
        self,
        *,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        chunks: list[Document] = []

        for doc in documents:
            text = doc.page_content
            if not text.strip():
                chunks.append(doc)
                continue

            if len(text) <= self._chunk_size:
                meta = self._merge_metadata(doc.metadata, 0)
                meta["split_method"] = "fixed"
                chunks.append(Document(page_content=text, metadata=meta))
                continue

            text_chunks = self._fixed_size_split(text)
            for i, chunk_text in enumerate(text_chunks):
                meta = self._merge_metadata(doc.metadata, len(chunks))
                meta["split_method"] = "fixed"
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
