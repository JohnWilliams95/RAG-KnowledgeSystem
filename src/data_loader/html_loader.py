from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry

try:
    import html2text as _html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

HTML_EXTENSIONS = [".html", ".htm"]


@loader_registry.register(extensions=HTML_EXTENSIONS)
class HTMLLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        prefer_html2text: bool = True,
        extract_links: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._prefer_html2text = prefer_html2text
        self._extract_links = extract_links

    def lazy_load(self) -> Iterator[Document]:
        raw_html = self._file_path.read_text(encoding="utf-8", errors="replace")

        if self._prefer_html2text and HAS_HTML2TEXT:
            text = self._html2text_convert(raw_html)
        elif HAS_BS4:
            text = self._beautifulsoup_extract(raw_html)
        else:
            text = self._regex_strip(raw_html)

        if not text.strip():
            return

        title = self._extract_title(raw_html)

        yield Document(
            page_content=text.strip(),
            metadata={
                "source_file": self._file_path.name,
                "content_type": "html",
                "title": title,
            },
        )

    def _html2text_convert(self, html: str) -> str:
        converter = _html2text.HTML2Text()
        converter.ignore_links = not self._extract_links
        converter.ignore_images = False
        converter.ignore_emphasis = False
        converter.body_width = 0
        return converter.handle(html)

    def _beautifulsoup_extract(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)

    def _regex_strip(self, html: str) -> str:
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in HTML_EXTENSIONS