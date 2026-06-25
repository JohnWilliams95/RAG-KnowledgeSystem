from backend.src.data_loader.base_loader import BaseDocumentLoader
from backend.src.data_loader.loader_registry import LoaderRegistry, loader_registry
from backend.src.data_loader.pdf_loader import PDFLoader
from backend.src.data_loader.word_loader import DocxLoader, DocLoader
from backend.src.data_loader.excel_loader import ExcelLoader, CSVLoader
from backend.src.data_loader.ppt_loader import PptxLoader
from backend.src.data_loader.image_loader import ImageLoader
from backend.src.data_loader.markdown_loader import MarkdownLoader
from backend.src.data_loader.text_loader import TextLoader
from backend.src.data_loader.html_loader import HTMLLoader
from backend.src.data_loader.code_loader import CodeLoader
from backend.src.data_loader.structured_loader import StructuredDataLoader
from backend.src.data_loader.web_scraper import WebScraper
from backend.src.data_loader.unstructured_loader import UnstructuredPDFLoader
from backend.src.data_loader.ocr_utils import ocr_image, ocr_pdf_page, is_scanned_page

__all__ = [
    "BaseDocumentLoader",
    "LoaderRegistry",
    "loader_registry",
    "PDFLoader",
    "DocxLoader",
    "DocLoader",
    "ExcelLoader",
    "CSVLoader",
    "PptxLoader",
    "ImageLoader",
    "MarkdownLoader",
    "TextLoader",
    "HTMLLoader",
    "CodeLoader",
    "StructuredDataLoader",
    "WebScraper",
    "UnstructuredPDFLoader",
    "ocr_image",
    "ocr_pdf_page",
    "is_scanned_page",
]