from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.documents import Document


class BaseSplitter(ABC):
    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        ...

    def _merge_metadata(self, parent_meta: dict, chunk_index: int) -> dict:
        meta = dict(parent_meta)
        meta["chunk_index"] = chunk_index
        return meta
