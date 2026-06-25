from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

from langchain_core.documents import Document


@dataclass
class LoaderMeta:
    source_path: Path
    file_type: str
    file_size: int
    page_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class BaseDocumentLoader(ABC):
    def __init__(self, file_path: Path, metadata: Optional[dict[str, Any]] = None):
        self._file_path = file_path
        self._metadata = metadata or {}

    @property
    def file_path(self) -> Path:
        return self._file_path

    @abstractmethod
    def lazy_load(self) -> Iterator[Document]:
        ...

    def load(self) -> list[Document]:
        docs = list(self.lazy_load())
        self._enrich_metadata(docs)
        return docs

    def _enrich_metadata(self, docs: list[Document]) -> None:
        base_meta = self._build_base_metadata()
        for doc in docs:
            doc.metadata.setdefault("source", str(self._file_path))
            doc.metadata.setdefault("file_type", base_meta.file_type)
            doc.metadata.setdefault("file_size", base_meta.file_size)
            for k, v in self._metadata.items():
                doc.metadata.setdefault(k, v)

    def _build_base_metadata(self) -> LoaderMeta:
        try:
            file_size = self._file_path.stat().st_size
        except OSError:
            file_size = 0
        return LoaderMeta(
            source_path=self._file_path,
            file_type=self._file_path.suffix.lower(),
            file_size=file_size,
        )

    @classmethod
    @abstractmethod
    def supports(cls, file_path: Path) -> bool:
        ...