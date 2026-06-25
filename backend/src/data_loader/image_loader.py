from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Iterator, Optional

from langchain_core.documents import Document

from backend.src.data_loader.base_loader import BaseDocumentLoader
from backend.src.data_loader.loader_registry import loader_registry
from backend.src.utils.ocr_utils import ocr_image

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]


@loader_registry.register(extensions=IMAGE_EXTENSIONS)
class ImageLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        use_ocr: bool = True,
        use_multimodal_llm: bool = False,
        ocr_lang: str = "chi_sim+eng",
    ):
        super().__init__(file_path, metadata)
        self._use_ocr = use_ocr
        self._use_multimodal_llm = use_multimodal_llm
        self._ocr_lang = ocr_lang

    def lazy_load(self) -> Iterator[Document]:
        if self._use_ocr:
            yield from self._ocr_extract()

        if self._use_multimodal_llm:
            yield from self._multimodal_extract()

        if not self._use_ocr and not self._use_multimodal_llm:
            yield Document(
                page_content=f"[Image file: {self._file_path.name}]",
                metadata={
                    "source_file": self._file_path.name,
                    "content_type": "image",
                    "extraction_method": "none",
                },
            )

    def _ocr_extract(self) -> Iterator[Document]:
        try:
            from PIL import Image

            img = Image.open(str(self._file_path))
            text, elapse = ocr_image(img)

            if text.strip():
                yield Document(
                    page_content=text.strip(),
                    metadata={
                        "source_file": self._file_path.name,
                        "content_type": "image_ocr",
                        "extraction_method": "rapidocr",
                        "ocr_lang": self._ocr_lang,
                        "ocr_time": round(elapse, 3),
                        "image_size": f"{img.width}x{img.height}",
                    },
                )
        except Exception as e:
            logger.warning(f"OCR extraction failed for {self._file_path.name}: {e}")

    def _multimodal_extract(self) -> Iterator[Document]:
        try:
            from PIL import Image

            img = Image.open(str(self._file_path))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

            yield Document(
                page_content=f"[Image: {self._file_path.name}]",
                metadata={
                    "source_file": self._file_path.name,
                    "content_type": "image_multimodal",
                    "extraction_method": "multimodal_llm",
                    "image_base64": b64,
                    "image_size": f"{img.width}x{img.height}",
                },
            )
        except Exception as e:
            logger.warning(f"Multimodal extraction failed for {self._file_path.name}: {e}")

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in IMAGE_EXTENSIONS