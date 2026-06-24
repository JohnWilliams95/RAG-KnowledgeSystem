from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry

CODE_EXTENSIONS = [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"]

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
}


@loader_registry.register(extensions=CODE_EXTENSIONS)
class CodeLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        include_comments: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._include_comments = include_comments

    def lazy_load(self) -> Iterator[Document]:
        try:
            text = self._file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        if not text.strip():
            return

        language = LANGUAGE_MAP.get(self._file_path.suffix.lower(), "unknown")

        lines = text.split("\n")
        code_lines = lines
        if not self._include_comments:
            code_lines = self._strip_comments(lines, language)

        filtered = "\n".join(code_lines)
        if not filtered.strip():
            filtered = text

        import_map = self._extract_imports(text, language)

        yield Document(
            page_content=filtered.strip(),
            metadata={
                "source_file": self._file_path.name,
                "content_type": "code",
                "language": language,
                "total_lines": len(lines),
                "imports": import_map,
            },
        )

    def _strip_comments(self, lines: list[str], language: str) -> list[str]:
        comment_prefixes = {"python": "#", "bash": "#", "rust": "//", "go": "//"}
        prefix = comment_prefixes.get(language, "//")

        if language == "python":
            return [l for l in lines if not l.strip().startswith("#")]

        return [
            l for l in lines
            if not l.strip().startswith(prefix)
            and not l.strip().startswith("/*")
            and not l.strip().startswith("*")
            and not l.strip().endswith("*/")
        ]

    def _extract_imports(self, text: str, language: str) -> str:
        import re

        patterns = {
            "python": r"^(?:import|from)\s+.+$",
            "javascript": r"^(?:import|require|const\s+.*require)\s+.+$",
            "typescript": r"^(?:import|require|const\s+.*require)\s+.+$",
            "java": r"^import\s+.+;$",
            "go": r"^(?:import|\".*\")\s*.*$",
            "rust": r"^use\s+.+;$",
            "cpp": r"^#include\s+.+$",
            "c": r"^#include\s+.+$",
        }

        pattern = patterns.get(language)
        if not pattern:
            return ""

        matches = re.findall(pattern, text, re.MULTILINE)
        return "\n".join(matches) if matches else ""

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in CODE_EXTENSIONS