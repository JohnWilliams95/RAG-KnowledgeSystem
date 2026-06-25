from __future__ import annotations

import re

from langchain_core.documents import Document

from backend.src.splitting.base_splitter import BaseSplitter
from backend.src.splitting.fixed_splitter import FixedSplitter


class HeadingSplitter(BaseSplitter):
    HEADING_PATTERNS = [
        r"^(#{1,6})\s+(.+)$",
        r"^(\d+(?:\.\d+)*)\s+(.+)$",
        r"^([一二三四五六七八九十]+[、.])\s*(.+)$",
        r"^(第[一二三四五六七八九十百千万]+[章节条款])\s*(.+)$",
        r"<h([1-6])>(.+)</h\1>",
    ]

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

            sections = self._split_by_headings(text)
            if len(sections) <= 1 and len(text) <= self._chunk_size:
                meta = self._merge_metadata(doc.metadata, 0)
                meta["split_method"] = "heading"
                chunks.append(Document(page_content=text, metadata=meta))
                continue

            for heading, content in sections:
                chunk_text = f"{heading}\n{content}" if heading else content
                if len(chunk_text) <= self._chunk_size:
                    meta = self._merge_metadata(doc.metadata, len(chunks))
                    meta["split_method"] = "heading"
                    meta["heading"] = heading
                    chunks.append(Document(page_content=chunk_text, metadata=meta))
                else:
                    sub_chunks = self._fixed_splitter._fixed_size_split(chunk_text)
                    for sub_chunk in sub_chunks:
                        meta = self._merge_metadata(doc.metadata, len(chunks))
                        meta["split_method"] = "heading_then_fixed"
                        meta["heading"] = heading
                        chunks.append(Document(page_content=sub_chunk, metadata=meta))

        return chunks

    def _split_by_headings(self, text: str) -> list[tuple[str, str]]:
        lines = text.split("\n")
        sections: list[tuple[str, str]] = []
        current_heading = ""
        current_content: list[str] = []

        for line in lines:
            if self._is_heading(line):
                if current_content:
                    sections.append((current_heading, "\n".join(current_content)))
                current_heading = line.strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content or current_heading:
            sections.append((current_heading, "\n".join(current_content)))

        return sections

    def _is_heading(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False

        for pattern in self.HEADING_PATTERNS:
            if re.match(pattern, line, re.MULTILINE):
                return True

        return False
