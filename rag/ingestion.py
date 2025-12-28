import chromadb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class KnowledgeBaseIngester:
    """Ingest documents into Chroma vector database"""

    def __init__(self, chroma_client, collection_name: str):
        """
        Initialize ingester

        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to create/use
        """
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> list:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Number of words per chunk
            overlap: Number of words to overlap between chunks

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def ingest_documents(self, docs_path: str):
        """
        Ingest all documents from directory

        Args:
            docs_path: Path to directory containing documents
        """
        documents = []
        metadatas = []
        ids = []

        docs_path_obj = Path(docs_path)
        if not docs_path_obj.exists():
            logger.error(f"Documents path does not exist: {docs_path}")
            return

        # Process all markdown files
        for file_path in docs_path_obj.rglob("*.md"):
            try:
                text = file_path.read_text(encoding='utf-8')
                chunks = self.chunk_text(text)

                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "source": str(file_path),
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "filename": file_path.name
                    })
                    ids.append(f"{file_path.stem}_{i}")

                logger.info(f"Processed {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        # Batch insert
        if documents:
            try:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Successfully ingested {len(documents)} document chunks")
            except Exception as e:
                logger.error(f"Error ingesting documents: {e}")
        else:
            logger.warning("No documents found to ingest")

    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Cleared collection: {self.collection.name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
