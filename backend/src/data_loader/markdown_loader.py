from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry


@loader_registry.register(extensions=[".md"])
class MarkdownLoader(BaseDocumentLoader):
    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def lazy_load(self) -> Iterator[Document]:
        text = self._file_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return

        sections = self._split_by_headings(text)

        for heading, content, level in sections:
            section_text = f"{'#' * level} {heading}\n{content}" if heading else content
            if not section_text.strip():
                continue

            yield Document(
                page_content=section_text.strip(),
                metadata={
                    "source_file": self._file_path.name,
                    "heading": heading,
                    "heading_level": level,
                    "content_type": "markdown",
                },
            )

    def _split_by_headings(self, text: str) -> list[tuple[str, str, int]]:
        headings = list(self._HEADING_PATTERN.finditer(text))

        if not headings:
            return [("", text, 0)]

        sections: list[tuple[str, str, int]] = []

        if headings[0].start() > 0:
            preamble = text[: headings[0].start()].strip()
            if preamble:
                sections.append(("", preamble, 0))

        for i, match in enumerate(headings):
            level = len(match.group(1))
            heading_text = match.group(2).strip()

            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            content = text[start:end].strip()

            sections.append((heading_text, content, level))

        return sections

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".md"