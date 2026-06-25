from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import settings
from src.config.constants import IngestionStatus

logger = logging.getLogger(__name__)


class MetadataStore:
    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or str(
            Path(settings.project_root) / "data" / "metadata.db"
        )
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._init_tables()
        return self._conn

    def _init_tables(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                file_hash TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_message TEXT,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                qdrant_point_id TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
            );

            CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
            CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
        """)
        conn.commit()

    def register_document(
        self,
        file_path: str | Path,
        *,
        file_type: str,
        file_size: int = 0,
        file_hash: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        with self._lock:
            conn = self._get_conn()
            file_path = str(file_path)
            file_name = Path(file_path).name

            if file_hash is None:
                file_hash = self._compute_file_hash(file_path)

            existing = conn.execute(
                "SELECT doc_id, status FROM documents WHERE file_hash = ?",
                (file_hash,),
            ).fetchone()

            if existing:
                return existing["doc_id"]

            doc_id = hashlib.sha256(f"{file_path}:{file_hash}".encode()).hexdigest()[:16]
            now = datetime.now(timezone.utc).isoformat()

            conn.execute(
                """INSERT INTO documents
                   (doc_id, file_path, file_name, file_type, file_size, file_hash,
                    chunk_count, status, created_at, updated_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)""",
                (
                    doc_id,
                    file_path,
                    file_name,
                    file_type,
                    file_size,
                    file_hash,
                    IngestionStatus.PENDING.value,
                    now,
                    now,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
            return doc_id

    def update_document_status(
        self,
        doc_id: str,
        status: IngestionStatus,
        *,
        chunk_count: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        with self._lock:
            conn = self._get_conn()
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """UPDATE documents
                   SET status = ?, chunk_count = ?, updated_at = ?, error_message = ?
                   WHERE doc_id = ?""",
                (status.value, chunk_count, now, error_message, doc_id),
            )
            conn.commit()

    def register_chunk(
        self,
        doc_id: str,
        chunk_index: int,
        content_hash: str,
        *,
        qdrant_point_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        with self._lock:
            conn = self._get_conn()
            chunk_id = hashlib.sha256(f"{doc_id}:{chunk_index}:{content_hash}".encode()).hexdigest()[:16]
            now = datetime.now(timezone.utc).isoformat()

            conn.execute(
                """INSERT OR REPLACE INTO chunks
                   (chunk_id, doc_id, chunk_index, content_hash, qdrant_point_id, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    chunk_id,
                    doc_id,
                    chunk_index,
                    content_hash,
                    qdrant_point_id,
                    now,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
            return chunk_id

    def get_document(self, doc_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def get_document_by_path(self, file_path: str | Path) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM documents WHERE file_path = ?", (str(file_path),)).fetchone()
        return dict(row) if row else None

    def is_file_processed(self, file_path: str | Path, file_hash: Optional[str] = None) -> bool:
        conn = self._get_conn()
        if file_hash:
            row = conn.execute(
                "SELECT status FROM documents WHERE file_hash = ?",
                (file_hash,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT status FROM documents WHERE file_path = ?",
                (str(file_path),),
            ).fetchone()
        return row is not None and row["status"] in (
            IngestionStatus.COMPLETED.value,
            IngestionStatus.PARTIAL.value,
        )

    def list_documents(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def count_documents(self, *, status: Optional[str] = None) -> int:
        conn = self._get_conn()
        if status:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE status = ?",
                (status,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
        return row["cnt"] if row else 0

    def delete_document(self, doc_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()

    @staticmethod
    def _compute_file_hash(file_path: str | Path, block_size: int = 8192) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                block = f.read(block_size)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None