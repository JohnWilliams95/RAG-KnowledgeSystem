from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from backend.src.data_loader.base_loader import BaseDocumentLoader

logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(
        self,
        *,
        max_depth: int = 2,
        max_pages: int = 50,
        timeout: int = 30,
        user_agent: str = "RAG-Bot/1.0",
    ):
        self._max_depth = max_depth
        self._max_pages = max_pages
        self._timeout = timeout
        self._user_agent = user_agent

    def scrape_url(self, url: str) -> list[Document]:
        return self._scrape_with_httpx(url)

    def scrape_site(
        self,
        start_url: str,
        *,
        url_prefix: Optional[str] = None,
    ) -> list[Document]:
        visited: set[str] = set()
        results: list[Document] = []
        queue: list[tuple[str, int]] = [(start_url, 0)]

        while queue and len(results) < self._max_pages:
            current_url, depth = queue.pop(0)

            if current_url in visited:
                continue
            if depth > self._max_depth:
                continue
            if url_prefix and not current_url.startswith(url_prefix):
                continue

            visited.add(current_url)
            docs = self.scrape_url(current_url)
            results.extend(docs)

            if depth < self._max_depth:
                links = self._extract_links(current_url)
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

        return results

    def _scrape_with_httpx(self, url: str) -> list[Document]:
        import httpx
        import re

        try:
            resp = httpx.get(
                url,
                timeout=self._timeout,
                headers={"User-Agent": self._user_agent},
                follow_redirects=True,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return []

        html = resp.text

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            title = soup.title.string.strip() if soup.title else ""
        except ImportError:
            text = re.sub(r"<[^>]+>", "\n", html)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            title = ""

        if not text.strip():
            return []

        return [
            Document(
                page_content=text.strip(),
                metadata={
                    "source": url,
                    "title": title,
                    "content_type": "web_page",
                    "url": url,
                },
            )
        ]

    def _extract_links(self, url: str) -> list[str]:
        import httpx
        import re
        from urllib.parse import urljoin, urlparse

        try:
            resp = httpx.get(url, timeout=self._timeout, follow_redirects=True)
        except Exception:
            return []

        link_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        raw_links = link_pattern.findall(resp.text)

        base_domain = urlparse(url).netloc
        resolved: list[str] = []

        for link in raw_links:
            full_url = urljoin(url, link)
            parsed = urlparse(full_url)
            if parsed.scheme in ("http", "https") and parsed.netloc == base_domain:
                resolved.append(full_url.split("#")[0].split("?")[0])

        return list(dict.fromkeys(resolved))