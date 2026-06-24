from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

import fitz
from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry


@loader_registry.register(extensions=[".pdf"])
class PDFLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        extract_images: bool = False,
        extract_tables: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._extract_images = extract_images
        self._extract_tables = extract_tables

    def lazy_load(self) -> Iterator[Document]:
        doc = fitz.open(str(self._file_path))
        try:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if not text.strip():
                    continue

                meta = {
                    "page": page_num,
                    "total_pages": doc.page_count,
                    "source_file": self._file_path.name,
                }

                yield Document(page_content=text.strip(), metadata=meta)

                if self._extract_tables:
                    yield from self._extract_page_tables(page, page_num, doc.page_count)

        finally:
            doc.close()

    def _extract_page_tables(
        self,
        page: fitz.Page,
        page_num: int,
        total_pages: int,
    ) -> Iterator[Document]:
        tables = page.find_tables()
        if tables is None:
            return
        for table_idx, table in enumerate(tables.tables):
            rows = table.extract()
            if not rows:
                continue
            header = rows[0] if rows else []
            lines: list[str] = []
            for row in rows:
                cells = [str(cell) if cell is not None else "" for cell in row]
                lines.append(" | ".join(cells))
            table_text = "\n".join(lines)

            yield Document(
                page_content=f"[Table {table_idx + 1}]\n{table_text}",
                metadata={
                    "page": page_num,
                    "total_pages": total_pages,
                    "source_file": self._file_path.name,
                    "content_type": "table",
                    "table_index": table_idx,
                    "table_header": " | ".join(str(h) if h is not None else "" for h in header),
                },
            )

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"