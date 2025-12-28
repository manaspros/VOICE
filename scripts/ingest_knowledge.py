"""
Knowledge Base Ingestion Script

This script ingests documents from the knowledge_base directory
into the Chroma vector database for RAG retrieval.

Usage:
    python scripts/ingest_knowledge.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from rag.ingestion import KnowledgeBaseIngester
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Ingest knowledge base into Chroma"""
    try:
        logger.info("Starting knowledge base ingestion...")
        logger.info(f"Chroma persist directory: {settings.chroma_persist_dir}")
        logger.info(f"Collection name: {settings.chroma_collection_name}")

        # Initialize Chroma client
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info("Chroma client initialized")

        # Create ingester
        ingester = KnowledgeBaseIngester(client, settings.chroma_collection_name)

        # Ingest documents from knowledge_base directory
        ingester.ingest_documents("./knowledge_base")

        # Get collection stats
        count = ingester.collection.count()
        logger.info(f"✓ Ingestion complete! Total documents in collection: {count}")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
