from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Type

from src.config.constants import EXTENSION_MAP
from src.data_loader.base_loader import BaseDocumentLoader

logger = logging.getLogger(__name__)


class LoaderRegistry:
    _loaders: dict[str, Type[BaseDocumentLoader]] = {}

    @classmethod
    def register(cls, *, extensions: list[str]):
        def decorator(loader_cls: Type[BaseDocumentLoader]) -> Type[BaseDocumentLoader]:
            for ext in extensions:
                ext = ext.lower()
                if not ext.startswith("."):
                    ext = f".{ext}"
                cls._loaders[ext] = loader_cls
            return loader_cls
        return decorator

    @classmethod
    def get_loader(cls, file_path: Path) -> Optional[Type[BaseDocumentLoader]]:
        suffix = file_path.suffix.lower()
        if suffix in cls._loaders:
            return cls._loaders[suffix]
        if f".{file_path.name.lower()}" in cls._loaders:
            return cls._loaders[file_path.name.lower()]
        return None

    @classmethod
    def create_loader(
        cls,
        file_path: Path,
        metadata: Optional[dict] = None,
    ) -> Optional[BaseDocumentLoader]:
        loader_cls = cls.get_loader(file_path)
        if loader_cls is None:
            logger.warning(f"No loader registered for: {file_path}")
            return None
        return loader_cls(file_path, metadata=metadata)

    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        suffix = file_path.suffix.lower()
        return suffix in cls._loaders

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return set(cls._loaders.keys())


loader_registry = LoaderRegistry()