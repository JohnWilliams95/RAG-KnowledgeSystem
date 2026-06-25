from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

import yaml
from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry

STRUCTURED_EXTENSIONS = [".json", ".yaml", ".yml"]


@loader_registry.register(extensions=STRUCTURED_EXTENSIONS)
class StructuredDataLoader(BaseDocumentLoader):
    def lazy_load(self) -> Iterator[Document]:
        suffix = self._file_path.suffix.lower()
        text = self._file_path.read_text(encoding="utf-8", errors="replace")

        if suffix == ".json":
            yield from self._parse_json(text)
        elif suffix in (".yaml", ".yml"):
            yield from self._parse_yaml(text)

    def _parse_json(self, text: str) -> Iterator[Document]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            yield Document(
                page_content=f"[Invalid JSON: {e}]",
                metadata={"source_file": self._file_path.name, "error": "json_parse_failed"},
            )
            return

        if isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    yield from self._flatten_dict(item, index=idx)
                else:
                    yield Document(
                        page_content=str(item),
                        metadata={
                            "source_file": self._file_path.name,
                            "content_type": "json_array_item",
                            "index": idx,
                        },
                    )
        elif isinstance(data, dict):
            yield from self._flatten_dict(data)
        else:
            yield Document(
                page_content=json.dumps(data, ensure_ascii=False, indent=2),
                metadata={"source_file": self._file_path.name, "content_type": "json_scalar"},
            )

    def _parse_yaml(self, text: str) -> Iterator[Document]:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            yield Document(
                page_content=f"[Invalid YAML: {e}]",
                metadata={"source_file": self._file_path.name, "error": "yaml_parse_failed"},
            )
            return

        if isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    yield from self._flatten_dict(item, index=idx)
                else:
                    yield Document(
                        page_content=str(item),
                        metadata={
                            "source_file": self._file_path.name,
                            "content_type": "yaml_list_item",
                            "index": idx,
                        },
                    )
        elif isinstance(data, dict):
            yield from self._flatten_dict(data)
        else:
            yield Document(
                page_content=str(data),
                metadata={"source_file": self._file_path.name, "content_type": "yaml_scalar"},
            )

    def _flatten_dict(
        self,
        data: dict,
        prefix: str = "",
        index: Optional[int] = None,
    ) -> Iterator[Document]:
        flat_parts: list[str] = []

        def _flatten(obj, parent_key: str = ""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    _flatten(v, new_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{parent_key}[{i}]"
                    _flatten(item, new_key)
            else:
                flat_parts.append(f"{parent_key}: {obj}")

        _flatten(data)

        if not flat_parts:
            return

        meta = {
            "source_file": self._file_path.name,
            "content_type": "structured",
        }
        if index is not None:
            meta["index"] = index
        if prefix:
            meta["prefix"] = prefix

        yield Document(
            page_content="\n".join(flat_parts),
            metadata=meta,
        )

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in STRUCTURED_EXTENSIONS