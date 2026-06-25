from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from backend.src.data_loader.base_loader import BaseDocumentLoader
from backend.src.data_loader.loader_registry import loader_registry

TEXT_EXTENSIONS = [".txt", ".log", ".rst"]


@loader_registry.register(extensions=TEXT_EXTENSIONS)
class TextLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        encoding: str = "utf-8",
    ):
        super().__init__(file_path, metadata)
        self._encoding = encoding

    def lazy_load(self) -> Iterator[Document]:
        try:
            text = self._file_path.read_text(encoding=self._encoding, errors="replace")
        except Exception:
            text = self._file_path.read_text(encoding="gbk", errors="replace")

        if not text.strip():
            return

        line_count = text.count("\n") + 1

        yield Document(
            page_content=text.strip(),
            metadata={
                "source_file": self._file_path.name,
                "line_count": line_count,
                "content_type": "text",
            },
        )

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in TEXT_EXTENSIONS