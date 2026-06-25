#!/usr/bin/env python3
"""Rebuild the entire Qdrant index from scratch."""

from __future__ import annotations

import argparse
import logging

from src.config import settings
from backend.src.ingestion.document_store import DocumentStore
from backend.src.ingestion.metadata_store import MetadataStore
from backend.src.ingestion.pipeline import IngestionPipeline
from backend.src.embedding.bge_embedding import BGEM3Embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Rebuild Qdrant index")
    parser.add_argument("--confirm", action="store_true", help="Confirm rebuild")
    args = parser.parse_args()

    if not args.confirm:
        print("This will DELETE the existing collection and rebuild from scratch.")
        print("Use --confirm to proceed.")
        return

    settings.ensure_directories()

    embedding_model = BGEM3Embedding()
    doc_store = DocumentStore(embedding_model=embedding_model)
    meta_store = MetadataStore()

    if doc_store.client.collection_exists(settings.qdrant_collection_name):
        logger.info(f"Deleting collection '{settings.qdrant_collection_name}'...")
        doc_store.client.delete_collection(settings.qdrant_collection_name)

    doc_store.init_collection()
    logger.info("Collection recreated")

    pipeline = IngestionPipeline(doc_store, meta_store, skip_processed=False)

    import json
    docs = meta_store.list_documents(limit=100000)
    for doc_info in docs:
        file_path = doc_info.get("file_path", "")
        if file_path:
            result = pipeline.ingest_file(file_path)
            logger.info(f"Re-ingested {file_path}: {result.get('status')}")

    meta_store.close()
    logger.info("Rebuild complete")


if __name__ == "__main__":
    main()