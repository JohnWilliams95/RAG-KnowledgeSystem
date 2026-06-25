from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader

logger = logging.getLogger(__name__)


class UnstructuredPDFLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        strategy: str = "auto",
        languages: Optional[list[str]] = None,
        include_page_breaks: bool = True,
        extract_images: bool = True,
        infer_table_structure: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._strategy = strategy
        self._languages = languages or ["chi_sim", "eng"]
        self._include_page_breaks = include_page_breaks
        self._extract_images = extract_images
        self._infer_table_structure = infer_table_structure

    def lazy_load(self) -> Iterator[Document]:
        try:
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(
                filename=str(self._file_path),
                strategy=self._strategy,
                languages=self._languages,
                include_page_breaks=self._include_page_breaks,
                extract_images_in_pdf=self._extract_images,
                infer_table_structure=self._infer_table_structure,
            )

            current_page = 1
            for element in elements:
                element_type = type(element).__name__
                text = str(element).strip()

                if not text:
                    continue

                page_num = getattr(element.metadata, "page_number", current_page) or current_page
                if hasattr(element.metadata, "page_number") and element.metadata.page_number:
                    current_page = element.metadata.page_number

                content_type = self._map_element_type(element_type)

                meta = {
                    "page": page_num,
                    "source_file": self._file_path.name,
                    "content_type": content_type,
                    "element_type": element_type,
                }

                if hasattr(element.metadata, "coordinates") and element.metadata.coordinates:
                    meta["has_coordinates"] = True

                if content_type == "table" and hasattr(element.metadata, "text_as_html"):
                    html = getattr(element.metadata, "text_as_html", None)
                    if html:
                        meta["table_html"] = html

                yield Document(page_content=text, metadata=meta)

        except ImportError:
            logger.warning("unstructured not installed. Falling back to PyMuPDF.")
            yield from self._fallback_pymupdf()
        except Exception as e:
            logger.warning(f"UnstructuredIO failed: {e}. Falling back to PyMuPDF.")
            yield from self._fallback_pymupdf()

    def _fallback_pymupdf(self) -> Iterator[Document]:
        import fitz
        doc = fitz.open(str(self._file_path))
        try:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    yield Document(
                        page_content=text,
                        metadata={
                            "page": page_num,
                            "total_pages": doc.page_count,
                            "source_file": self._file_path.name,
                            "content_type": "text",
                        },
                    )
        finally:
            doc.close()

    @staticmethod
    def _map_element_type(element_type: str) -> str:
        mapping = {
            "Title": "title",
            "NarrativeText": "text",
            "ListItem": "list",
            "Table": "table",
            "Image": "image",
            "FigureCaption": "caption",
            "Header": "header",
            "Footer": "footer",
            "PageBreak": "page_break",
            "Address": "address",
            "EmailAddress": "email",
            "Formula": "formula",
            "CodeSnippet": "code",
        }
        return mapping.get(element_type, "text")

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"