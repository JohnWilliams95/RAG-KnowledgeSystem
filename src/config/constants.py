from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    PPTX = "pptx"
    PPT = "ppt"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    BMP = "bmp"
    TIFF = "tiff"
    MD = "md"
    TXT = "txt"
    LOG = "log"
    RST = "rst"
    HTML = "html"
    HTM = "htm"
    PY = "py"
    JS = "js"
    TS = "ts"
    TSX = "tsx"
    JAVA = "java"
    GO = "go"
    RS = "rs"
    CPP = "cpp"
    C = "c"
    H = "h"
    JSON = "json"
    YAML = "yaml"
    YML = "yml"

    @classmethod
    def from_extension(cls, ext: str) -> "FileType | None":
        ext = ext.lstrip(".").lower()
        try:
            return cls(ext)
        except ValueError:
            return None


EXTENSION_MAP: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".doc": FileType.DOC,
    ".xlsx": FileType.XLSX,
    ".xls": FileType.XLS,
    ".csv": FileType.CSV,
    ".pptx": FileType.PPTX,
    ".ppt": FileType.PPT,
    ".png": FileType.PNG,
    ".jpg": FileType.JPG,
    ".jpeg": FileType.JPEG,
    ".bmp": FileType.BMP,
    ".tiff": FileType.TIFF,
    ".tif": FileType.TIFF,
    ".md": FileType.MD,
    ".txt": FileType.TXT,
    ".log": FileType.LOG,
    ".rst": FileType.RST,
    ".html": FileType.HTML,
    ".htm": FileType.HTM,
    ".py": FileType.PY,
    ".js": FileType.JS,
    ".ts": FileType.TS,
    ".tsx": FileType.TSX,
    ".java": FileType.JAVA,
    ".go": FileType.GO,
    ".rs": FileType.RS,
    ".cpp": FileType.CPP,
    ".c": FileType.C,
    ".h": FileType.H,
    ".json": FileType.JSON,
    ".yaml": FileType.YAML,
    ".yml": FileType.YML,
}

SUPPORTED_EXTENSIONS = frozenset(EXTENSION_MAP.keys())


class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 200

CODE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"
})

IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"
})

OFFICE_EXTENSIONS: frozenset[str] = frozenset({
    ".docx", ".doc", ".xlsx", ".xls", ".csv", ".pptx", ".ppt"
})