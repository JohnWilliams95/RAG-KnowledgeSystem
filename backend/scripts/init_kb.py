#!/usr/bin/env python3
"""Initialize knowledge base: create Qdrant collection and load documents."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import settings
from backend.src.ingestion.document_store import DocumentStore
from backend.src.ingestion.metadata_store import MetadataStore
from backend.src.ingestion.pipeline import IngestionPipeline
from backend.src.embedding.bge_embedding import BGEM3Embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Initialize RAG knowledge base")
    parser.add_argument("--data-dir", type=str, default="./data/raw", help="Data directory")
    parser.add_argument("--recursive", action="store_true", default=True, help="Recursive scan")
    parser.add_argument("--skip-processed", action="store_true", default=True, help="Skip processed files")
    parser.add_argument("--use-memory", action="store_true", default=False, help="Use in-memory Qdrant")
    args = parser.parse_args()

    settings.qdrant_use_memory = args.use_memory
    settings.ensure_directories()

    embedding_model = BGEM3Embedding()
    doc_store = DocumentStore(embedding_model=embedding_model)
    meta_store = MetadataStore()
    pipeline = IngestionPipeline(doc_store, meta_store, skip_processed=args.skip_processed)

    doc_store.init_collection()
    logger.info("Qdrant collection initialized")

    data_dir = Path(args.data_dir)
    if data_dir.exists():
        result = pipeline.ingest_directory(data_dir, recursive=args.recursive)
        logger.info(f"Ingestion result: {result}")
    else:
        logger.warning(f"Data directory not found: {data_dir}")
        logger.info("Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)

    info = doc_store.get_collection_info()
    logger.info(f"Collection info: {info}")

    meta_store.close()


if __name__ == "__main__":
    main()