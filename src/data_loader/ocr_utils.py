from __future__ import annotations

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_ocr_engine = None


def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine

    try:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
        logger.info("RapidOCR engine initialized")
        return _ocr_engine
    except ImportError:
        logger.warning("rapidocr-onnxruntime not installed. OCR disabled.")
        return None


def ocr_image(
    image: Image.Image | np.ndarray | bytes | str,
    *,
    lang: Optional[str] = None,
) -> tuple[str, float]:
    engine = _get_ocr_engine()
    if engine is None:
        return "", 0.0

    try:
        if isinstance(image, Image.Image):
            image = np.array(image)
        elif isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
            image = np.array(image)

        result, elapse = engine(image)

        if result is None:
            return "", 0.0

        texts = []
        for line in result:
            if line and len(line) >= 2:
                text = line[0] if isinstance(line[0], str) else str(line[0])
                texts.append(text)

        return "\n".join(texts), elapse or 0.0

    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return "", 0.0


def ocr_pdf_page(
    page,
    *,
    dpi: int = 300,
    lang: Optional[str] = None,
) -> tuple[str, float]:
    try:
        mat = page.get_pixmap(dpi=dpi)
        img_bytes = mat.tobytes("png")
        return ocr_image(img_bytes, lang=lang)
    except Exception as e:
        logger.warning(f"PDF page OCR failed: {e}")
        return "", 0.0


def is_scanned_page(page, *, text_threshold: int = 50) -> bool:
    text = page.get_text("text").strip()
    return len(text) < text_threshold