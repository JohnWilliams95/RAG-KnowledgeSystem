# Splitting Module Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the splitting module to have one class per file, and add three new splitting strategies (FixedSplitter, ParagraphSplitter, HeadingSplitter).

**Architecture:** Extract each splitter class into its own file with a `_splitter.py` suffix. Add new splitting strategies as independent classes. Update the factory to auto-select based on document features.

**Tech Stack:** Python, LangChain, FlagEmbedding

---

## File Structure

```
src/splitting/
├── __init__.py                 # Update exports
├── base_splitter.py            # BaseSplitter abstract base class
├── fixed_splitter.py           # NEW: FixedSplitter
├── paragraph_splitter.py       # NEW: ParagraphSplitter
├── heading_splitter.py         # NEW: HeadingSplitter
├── semantic_splitter.py        # SemanticSplitter (existing)
├── recursive_splitter.py       # RecursiveSplitter (existing)
├── code_splitter.py            # CodeSplitter (existing)
└── splitter_factory.py         # Update factory logic
```

---

### Task 1: Create base_splitter.py

**Files:**
- Create: `src/splitting/base_splitter.py`

- [ ] **Step 1: Create base_splitter.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/base_splitter.py
git commit -m "refactor: extract BaseSplitter to base_splitter.py"
```

---

### Task 2: Create fixed_splitter.py

**Files:**
- Create: `src/splitting/fixed_splitter.py`

- [ ] **Step 1: Create fixed_splitter.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/fixed_splitter.py
git commit -m "feat: add FixedSplitter for fixed-length chunking"
```

---

### Task 3: Create paragraph_splitter.py

**Files:**
- Create: `src/splitting/paragraph_splitter.py`

- [ ] **Step 1: Create paragraph_splitter.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/paragraph_splitter.py
git commit -m "feat: add ParagraphSplitter for paragraph-based chunking"
```

---

### Task 4: Create heading_splitter.py

**Files:**
- Create: `src/splitting/heading_splitter.py`

- [ ] **Step 1: Create heading_splitter.py**

```python
from __future__ import annotations

import re

from langchain_core.documents import Document

from src.splitting.base_splitter import BaseSplitter
from src.splitting.fixed_splitter import FixedSplitter


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
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/heading_splitter.py
git commit -m "feat: add HeadingSplitter for heading-based chunking"
```

---

### Task 5: Create semantic_splitter.py (refactor)

**Files:**
- Create: `src/splitting/semantic_splitter.py` (overwrite existing)

- [ ] **Step 1: Create semantic_splitter.py**

```python
from __future__ import annotations

import logging

from langchain_core.documents import Document

from src.config import settings
from src.splitting.base_splitter import BaseSplitter

logger = logging.getLogger(__name__)


class SemanticSplitter(BaseSplitter):
    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-m3",
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        similarity_threshold: float = 0.5,
        buffer_size: int = 1,
        device: str = "cpu",
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._similarity_threshold = similarity_threshold
        self._buffer_size = buffer_size
        self._model_name = model_name
        self._device = device
        self._embedder = None

    def _init_embedder(self):
        if self._embedder is not None:
            return
        from FlagEmbedding import FlagModel

        self._embedder = FlagModel(
            self._model_name,
            query_instruction_for_retrieval="",
            use_fp16=(self._device != "cpu"),
            devices=self._device,
        )
        logger.info(f"Semantic splitter embedder loaded: {self._model_name}")

    def split(self, documents: list[Document]) -> list[Document]:
        self._init_embedder()
        result: list[Document] = []

        for doc in documents:
            chunks = self._split_document(doc)
            result.extend(chunks)

        return result

    def _split_document(self, doc: Document) -> list[Document]:
        text = doc.page_content
        if not text.strip():
            return [doc]

        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [doc]

        if len(text) <= self._chunk_size:
            return [doc]

        embeddings = self._embedder.encode(sentences)["dense_embeds"]
        import numpy as np

        embeddings = np.array(embeddings)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normed = embeddings / norms

        split_points = self._detect_boundaries(normed)

        chunks = self._merge_sentences(sentences, split_points, doc)
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        import re

        pattern = r"(?<=[。！？.!?\n])\s*"
        parts = re.split(pattern, text)
        return [p.strip() for p in parts if p.strip()]

    def _detect_boundaries(self, normed_embeddings) -> list[int]:
        import numpy as np

        split_points: list[int] = []
        for i in range(len(normed_embeddings) - 1):
            sim = float(np.dot(normed_embeddings[i], normed_embeddings[i + 1]))
            if sim < self._similarity_threshold:
                split_points.append(i + 1)
        return split_points

    def _merge_sentences(
        self,
        sentences: list[str],
        split_points: list[int],
        doc: Document,
    ) -> list[Document]:
        boundaries = [0] + split_points + [len(sentences)]
        chunks: list[Document] = []

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_text = " ".join(sentences[start:end])

            if len(chunk_text) > self._chunk_size * 2:
                from src.splitting.fixed_splitter import FixedSplitter

                fixed_splitter = FixedSplitter(
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )
                sub_chunks = fixed_splitter._fixed_size_split(chunk_text)
                for j, sub in enumerate(sub_chunks):
                    meta = self._merge_metadata(doc.metadata, len(chunks))
                    meta["split_method"] = "semantic_then_fixed"
                    chunks.append(Document(page_content=sub, metadata=meta))
            else:
                meta = self._merge_metadata(doc.metadata, len(chunks))
                meta["split_method"] = "semantic"
                chunks.append(Document(page_content=chunk_text, metadata=meta))

        return chunks
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/semantic_splitter.py
git commit -m "refactor: extract SemanticSplitter to semantic_splitter.py"
```

---

### Task 6: Create recursive_splitter.py

**Files:**
- Create: `src/splitting/recursive_splitter.py`

- [ ] **Step 1: Create recursive_splitter.py**

```python
from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document

from src.splitting.base_splitter import BaseSplitter


class RecursiveSplitter(BaseSplitter):
    DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]

    def __init__(
        self,
        *,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or self.DEFAULT_SEPARATORS

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=self._separators,
            length_function=len,
            is_separator_regex=False,
        )

        chunks: list[Document] = []
        for doc in documents:
            split_docs = splitter.split_documents([doc])
            for i, chunk in enumerate(split_docs):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["split_method"] = "recursive"
                chunks.append(chunk)

        return chunks
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/recursive_splitter.py
git commit -m "refactor: extract RecursiveSplitter to recursive_splitter.py"
```

---

### Task 7: Create code_splitter.py

**Files:**
- Create: `src/splitting/code_splitter.py`

- [ ] **Step 1: Create code_splitter.py**

```python
from __future__ import annotations

from langchain_core.documents import Document

from src.splitting.base_splitter import BaseSplitter


class CodeSplitter(BaseSplitter):
    LANGUAGE_MAP = {
        "python": "python",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "go": "go",
        "rust": "rust",
        "cpp": "cpp",
        "c": "c",
    }

    def __init__(
        self,
        *,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        from langchain_text_splitters import (
            Language,
            RecursiveCharacterTextSplitter,
        )

        chunks: list[Document] = []
        for doc in documents:
            language_str = doc.metadata.get("language", "python")
            lang_enum = self._resolve_language(language_str)

            if lang_enum:
                splitter = RecursiveCharacterTextSplitter.from_language(
                    language=lang_enum,
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )

            split_docs = splitter.split_documents([doc])
            for i, chunk in enumerate(split_docs):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["split_method"] = "code_aware"
                chunks.append(chunk)

        return chunks

    def _resolve_language(self, language_str: str):
        from langchain_text_splitters import Language

        lookup = {
            "python": Language.PYTHON,
            "javascript": Language.JS,
            "js": Language.JS,
            "typescript": Language.TS,
            "ts": Language.TS,
            "java": Language.JAVA,
            "go": Language.GO,
            "rust": Language.RUST,
            "cpp": Language.CPP,
            "c": Language.C,
        }
        return lookup.get(language_str.lower())
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/code_splitter.py
git commit -m "refactor: extract CodeSplitter to code_splitter.py"
```

---

### Task 8: Update splitter_factory.py

**Files:**
- Modify: `src/splitting/splitter_factory.py`

- [ ] **Step 1: Update splitter_factory.py**

```python
from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document

from src.config import settings
from src.config.constants import CODE_EXTENSIONS
from src.splitting.base_splitter import BaseSplitter
from src.splitting.semantic_splitter import SemanticSplitter
from src.splitting.recursive_splitter import RecursiveSplitter
from src.splitting.code_splitter import CodeSplitter
from src.splitting.heading_splitter import HeadingSplitter
from src.splitting.paragraph_splitter import ParagraphSplitter


class SplitterFactory:
    @staticmethod
    def create(
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> BaseSplitter:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap
        se = semantic_enabled if semantic_enabled is not None else settings.semantic_chunking_enabled

        if se:
            return SemanticSplitter(
                chunk_size=cs,
                chunk_overlap=co,
                device=settings.embedding_device,
                model_name=settings.embedding_model_name,
            )
        return RecursiveSplitter(chunk_size=cs, chunk_overlap=co)

    @staticmethod
    def create_for_documents(
        documents: list[Document],
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> list[BaseSplitter]:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap

        code_docs: list[Document] = []
        heading_docs: list[Document] = []
        regular_docs: list[Document] = []

        for doc in documents:
            lang = doc.metadata.get("language")
            ext = doc.metadata.get("file_type", "")
            if lang or ext in CODE_EXTENSIONS:
                code_docs.append(doc)
            elif ext in {".md", ".markdown", ".rst"}:
                heading_docs.append(doc)
            else:
                regular_docs.append(doc)

        splitters: list[BaseSplitter] = []
        if code_docs:
            splitters.append(CodeSplitter(chunk_size=max(cs, 1500), chunk_overlap=co))
        if heading_docs:
            splitters.append(HeadingSplitter(chunk_size=cs, chunk_overlap=co))
        if regular_docs:
            splitters.append(SplitterFactory.create(
                chunk_size=cs,
                chunk_overlap=co,
                semantic_enabled=semantic_enabled,
            ))
        return splitters

    @staticmethod
    def split_documents(
        documents: list[Document],
        *,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        semantic_enabled: Optional[bool] = None,
    ) -> list[Document]:
        cs = chunk_size or settings.chunk_size
        co = chunk_overlap or settings.chunk_overlap

        code_docs: list[Document] = []
        heading_docs: list[Document] = []
        regular_docs: list[Document] = []

        for doc in documents:
            lang = doc.metadata.get("language")
            ext = doc.metadata.get("file_type", "")
            if lang or ext in CODE_EXTENSIONS:
                code_docs.append(doc)
            elif ext in {".md", ".markdown", ".rst"}:
                heading_docs.append(doc)
            else:
                regular_docs.append(doc)

        all_chunks: list[Document] = []

        if code_docs:
            code_splitter = CodeSplitter(chunk_size=max(cs, 1500), chunk_overlap=co)
            all_chunks.extend(code_splitter.split(code_docs))

        if heading_docs:
            heading_splitter = HeadingSplitter(chunk_size=cs, chunk_overlap=co)
            all_chunks.extend(heading_splitter.split(heading_docs))

        if regular_docs:
            se = semantic_enabled if semantic_enabled is not None else settings.semantic_chunking_enabled
            regular_splitter = SplitterFactory.create(
                chunk_size=cs, chunk_overlap=co, semantic_enabled=se,
            )
            all_chunks.extend(regular_splitter.split(regular_docs))

        return all_chunks
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/splitter_factory.py
git commit -m "refactor: update SplitterFactory with new splitter imports"
```

---

### Task 9: Update __init__.py

**Files:**
- Modify: `src/splitting/__init__.py`

- [ ] **Step 1: Update __init__.py**

```python
from src.splitting.base_splitter import BaseSplitter
from src.splitting.fixed_splitter import FixedSplitter
from src.splitting.paragraph_splitter import ParagraphSplitter
from src.splitting.heading_splitter import HeadingSplitter
from src.splitting.semantic_splitter import SemanticSplitter
from src.splitting.recursive_splitter import RecursiveSplitter
from src.splitting.code_splitter import CodeSplitter
from src.splitting.splitter_factory import SplitterFactory

__all__ = [
    "BaseSplitter",
    "FixedSplitter",
    "ParagraphSplitter",
    "HeadingSplitter",
    "SemanticSplitter",
    "RecursiveSplitter",
    "CodeSplitter",
    "SplitterFactory",
]
```

- [ ] **Step 2: Commit**

```bash
git add src/splitting/__init__.py
git commit -m "refactor: update __init__.py with new exports"
```

---

### Task 10: Delete original semantic_splitter.py

**Files:**
- Delete: `src/splitting/semantic_splitter.py` (already overwritten in Task 5)

- [ ] **Step 1: Verify all imports work**

```bash
python -c "from src.splitting import BaseSplitter, FixedSplitter, ParagraphSplitter, HeadingSplitter, SemanticSplitter, RecursiveSplitter, CodeSplitter, SplitterFactory; print('All imports OK')"
```

- [ ] **Step 2: Run linting**

```bash
python -m ruff check src/splitting/
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "refactor: complete splitting module restructuring"
```

---

### Task 11: Verification

- [ ] **Step 1: Test FixedSplitter**

```python
from langchain_core.documents import Document
from src.splitting.fixed_splitter import FixedSplitter

splitter = FixedSplitter(chunk_size=100, chunk_overlap=20)
doc = Document(page_content="A" * 500, metadata={"source": "test.txt"})
chunks = splitter.split([doc])
assert len(chunks) > 1
print(f"FixedSplitter: {len(chunks)} chunks")
```

- [ ] **Step 2: Test ParagraphSplitter**

```python
from langchain_core.documents import Document
from src.splitting.paragraph_splitter import ParagraphSplitter

splitter = ParagraphSplitter(chunk_size=100, chunk_overlap=20)
doc = Document(page_content="Para1\n\nPara2\n\nPara3", metadata={"source": "test.txt"})
chunks = splitter.split([doc])
assert len(chunks) == 3
print(f"ParagraphSplitter: {len(chunks)} chunks")
```

- [ ] **Step 3: Test HeadingSplitter**

```python
from langchain_core.documents import Document
from src.splitting.heading_splitter import HeadingSplitter

splitter = HeadingSplitter(chunk_size=100, chunk_overlap=20)
doc = Document(page_content="# Title\nContent1\n## Subtitle\nContent2", metadata={"source": "test.md"})
chunks = splitter.split([doc])
assert len(chunks) >= 2
print(f"HeadingSplitter: {len(chunks)} chunks")
```

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/ -v
```
