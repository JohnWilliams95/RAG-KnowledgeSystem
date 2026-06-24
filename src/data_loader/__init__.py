from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import LoaderRegistry, loader_registry
from src.data_loader.pdf_loader import PDFLoader
from src.data_loader.word_loader import DocxLoader, DocLoader
from src.data_loader.excel_loader import ExcelLoader, CSVLoader
from src.data_loader.ppt_loader import PptxLoader
from src.data_loader.image_loader import ImageLoader
from src.data_loader.markdown_loader import MarkdownLoader
from src.data_loader.text_loader import TextLoader
from src.data_loader.html_loader import HTMLLoader
from src.data_loader.code_loader import CodeLoader
from src.data_loader.structured_loader import StructuredDataLoader
from src.data_loader.web_scraper import WebScraper
from src.data_loader.unstructured_loader import UnstructuredPDFLoader
from src.data_loader.ocr_utils import ocr_image, ocr_pdf_page, is_scanned_page

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