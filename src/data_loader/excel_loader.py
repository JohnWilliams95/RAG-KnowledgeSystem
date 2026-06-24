from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

import pandas as pd
from langchain_core.documents import Document

from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry


@loader_registry.register(extensions=[".xlsx"])
class ExcelLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        sheet_name: Optional[str | int | list] = None,
        include_header: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._sheet_name = sheet_name
        self._include_header = include_header

    def lazy_load(self) -> Iterator[Document]:
        sheets: dict[str, pd.DataFrame] = {}
        try:
            excel_file = pd.ExcelFile(str(self._file_path), engine="openpyxl")
            target_sheets = self._sheet_name or excel_file.sheet_names
            if isinstance(target_sheets, (str, int)):
                target_sheets = [target_sheets]

            for sheet in target_sheets:
                if isinstance(sheet, int) and sheet < len(excel_file.sheet_names):
                    sheet = excel_file.sheet_names[sheet]
                if sheet in excel_file.sheet_names:
                    df = pd.read_excel(str(self._file_path), sheet_name=sheet)
                    sheets[sheet] = df
        except Exception:
            yield Document(
                page_content=f"[Failed to parse Excel file: {self._file_path.name}]",
                metadata={"source_file": self._file_path.name, "error": "parse_failed"},
            )
            return

        for sheet_name, df in sheets.items():
            if df.empty:
                continue

            df = df.dropna(how="all")

            lines: list[str] = []
            if self._include_header and not df.empty:
                lines.append(" | ".join(str(col) for col in df.columns))

            for _, row in df.iterrows():
                cells = []
                for val in row:
                    if pd.isna(val):
                        cells.append("")
                    else:
                        cells.append(str(val).strip())
                if any(cells):
                    lines.append(" | ".join(cells))

            if not lines:
                continue

            yield Document(
                page_content=f"[Sheet: {sheet_name}]\n" + "\n".join(lines),
                metadata={
                    "source_file": self._file_path.name,
                    "sheet_name": sheet_name,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "file_type": "excel",
                },
            )

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".xlsx", ".xls")


@loader_registry.register(extensions=[".csv"])
class CSVLoader(BaseDocumentLoader):
    def __init__(
        self,
        file_path: Path,
        metadata: Optional[dict] = None,
        *,
        delimiter: str = ",",
        include_header: bool = True,
    ):
        super().__init__(file_path, metadata)
        self._delimiter = delimiter
        self._include_header = include_header

    def lazy_load(self) -> Iterator[Document]:
        try:
            df = pd.read_csv(str(self._file_path), sep=self._delimiter)
            df = df.dropna(how="all")
            if df.empty:
                return

            lines: list[str] = []
            if self._include_header:
                lines.append(" | ".join(str(col) for col in df.columns))

            for _, row in df.iterrows():
                cells = []
                for val in row:
                    if pd.isna(val):
                        cells.append("")
                    else:
                        cells.append(str(val).strip())
                if any(cells):
                    lines.append(" | ".join(cells))

            if lines:
                yield Document(
                    page_content=f"[CSV: {self._file_path.name}]\n" + "\n".join(lines),
                    metadata={
                        "source_file": self._file_path.name,
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "file_type": "csv",
                    },
                )

        except Exception:
            yield Document(
                page_content=f"[Failed to parse CSV file: {self._file_path.name}]",
                metadata={"source_file": self._file_path.name, "error": "parse_failed"},
            )

    @classmethod
    def supports(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".csv"