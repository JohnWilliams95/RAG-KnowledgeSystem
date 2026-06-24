from __future__ import annotations

from langchain_core.documents import Document

from src.splitting.base_splitter import BaseSplitter
from src.splitting.fixed_splitter import FixedSplitter


class ParagraphSplitter(BaseSplitter):
    def __init__(
        self,
        *,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._fixed_splitter = FixedSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split(self, documents: list[Document]) -> list[Document]:
        chunks: list[Document] = []

        for doc in documents:
            text = doc.page_content
            if not text.strip():
                chunks.append(doc)
                continue

            paragraphs = self._split_paragraphs(text)
            if len(paragraphs) <= 1 and len(text) <= self._chunk_size:
                meta = self._merge_metadata(doc.metadata, 0)
                meta["split_method"] = "paragraph"
                chunks.append(Document(page_content=text, metadata=meta))
                continue

            for paragraph in paragraphs:
                if len(paragraph) <= self._chunk_size:
                    meta = self._merge_metadata(doc.metadata, len(chunks))
                    meta["split_method"] = "paragraph"
                    chunks.append(Document(page_content=paragraph, metadata=meta))
                else:
                    sub_chunks = self._fixed_splitter._fixed_size_split(paragraph)
                    for sub_chunk in sub_chunks:
                        meta = self._merge_metadata(doc.metadata, len(chunks))
                        meta["split_method"] = "paragraph_then_fixed"
                        chunks.append(Document(page_content=sub_chunk, metadata=meta))

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        parts = text.split("\n\n")
        return [p.strip() for p in parts if p.strip()]
