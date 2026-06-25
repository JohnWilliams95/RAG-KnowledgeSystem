from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Iterator, Optional

import fitz
from langchain_core.documents import Document

from backend.src.data_loader.base_loader import BaseDocumentLoader
from backend.src.data_loader.loader_registry import loader_registry
from backend.src.data_loader.ocr_utils import ocr_pdf_page, is_scanned_page

logger = logging.getLogger(__name__)


@loader_registry.register(extensions=[".pdf"])
class PDFLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        extract_images: bool = True,
        extract_tables: bool = True,
        ocr_scanned_pages: bool = True,
        ocr_dpi: int = 300,
        use_unstructured: bool = False,
        unstructured_strategy: str = "auto",
    ):
        super().__init__(file_path, metadata)
        self._extract_images = extract_images
        self._extract_tables = extract_tables
        self._ocr_scanned_pages = ocr_scanned_pages
        self._ocr_dpi = ocr_dpi
        self._use_unstructured = use_unstructured
        self._unstructured_strategy = unstructured_strategy

    def lazy_load(self) -> Iterator[Document]:
        if self._use_unstructured:
            yield from self._load_with_unstructured()
        else:
            yield from self._load_with_pymupdf()

    def _load_with_unstructured(self) -> Iterator[Document]:
        try:
            from backend.src.data_loader.unstructured_loader import UnstructuredPDFLoader
            loader = UnstructuredPDFLoader(
                self._file_path,
                metadata=self._metadata,
                strategy=self._unstructured_strategy,
            )
            yield from loader.lazy_load()
        except ImportError:
            logger.warning("unstructured not installed, falling back to PyMuPDF")
            yield from self._load_with_pymupdf()
        except Exception as e:
            logger.warning(f"UnstructuredIO failed: {e}, falling back to PyMuPDF")
            yield from self._load_with_pymupdf()

    def _load_with_pymupdf(self) -> Iterator[Document]:
        doc = fitz.open(str(self._file_path))
        try:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                is_scanned = self._ocr_scanned_pages and is_scanned_page(page)

                if is_scanned:
                    ocr_text, elapse = ocr_pdf_page(page, dpi=self._ocr_dpi)
                    if ocr_text.strip():
                        yield Document(
                            page_content=ocr_text.strip(),
                            metadata={
                                "page": page_num,
                                "total_pages": doc.page_count,
                                "source_file": self._file_path.name,
                                "content_type": "ocr_text",
                                "ocr_elapsed": elapse,
                            },
                        )
                    continue

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

                if self._extract_tables:
                    yield from self._extract_page_tables(page, page_num, doc.page_count)

                if self._extract_images:
                    yield from self._extract_page_images(page, page_num, doc.page_count)

        finally:
            doc.close()

    def _extract_page_tables(
        self,
        page: fitz.Page,
        page_num: int,
        total_pages: int,
    ) -> Iterator[Document]:
        tables = page.find_tables()
        if tables is None:
            return
        for table_idx, table in enumerate(tables.tables):
            rows = table.extract()
            if not rows:
                continue
            header = rows[0] if rows else []
            lines: list[str] = []
            for row in rows:
                cells = [str(cell) if cell is not None else "" for cell in row]
                lines.append(" | ".join(cells))
            table_text = "\n".join(lines)

            yield Document(
                page_content=f"[Table {table_idx + 1}]\n{table_text}",
                metadata={
                    "page": page_num,
                    "total_pages": total_pages,
                    "source_file": self._file_path.name,
                    "content_type": "table",
                    "table_index": table_idx,
                    "table_header": " | ".join(str(h) if h is not None else "" for h in header),
                },
            )

    def _extract_page_images(
        self,
        page: fitz.Page,
        page_num: int,
        total_pages: int,
    ) -> Iterator[Document]:
        image_list = page.get_images(full=True)
        if not image_list:
            return

        for img_idx, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = page.parent.extract_image(xref)
                if not base_image:
                    continue

                img_bytes = base_image["image"]
                img_ext = base_image.get("ext", "png")
                img_width = base_image.get("width", 0)
                img_height = base_image.get("height", 0)

                if img_width < 50 or img_height < 50:
                    continue

                b64_str = base64.b64encode(img_bytes).decode("utf-8")

                ocr_text = ""
                if self._ocr_scanned_pages:
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(img_bytes))
                        from backend.src.data_loader.ocr_utils import ocr_image
                        ocr_text, _ = ocr_image(img)
                    except Exception:
                        pass

                page_content = f"[Image {img_idx + 1} on page {page_num}]"
                if ocr_text.strip():
                    page_content += f"\nOCR Content: {ocr_text.strip()}"

                yield Document(
                    page_content=page_content,
                    metadata={
                        "page": page_num,
                        "total_pages": total_pages,
                        "source_file": self._file_path.name,
                        "content_type": "image",
                        "image_index": img_idx,
                        "image_format": img_ext,
                        "image_size": f"{img_width}x{img_height}",
                        "image_base64": b64_str,
                        "image_ocr_text": ocr_text.strip() if ocr_text.strip() else None,
                    },
                )

            except Exception as e:
                logger.warning(f"Failed to extract image {img_idx} on page {page_num}: {e}")

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"