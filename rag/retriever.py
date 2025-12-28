import chromadb
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieve relevant documents from Chroma vector database"""

    def __init__(self, chroma_client, collection_name: str):
        """
        Initialize retriever

        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to query
        """
        try:
            self.collection = chroma_client.get_collection(collection_name)
            logger.info(f"Initialized RAG retriever with collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error initializing RAG retriever: {e}")
            raise

    async def retrieve(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Retrieve top-k relevant documents

        Args:
            query: Search query text
            n_results: Number of results to return

        Returns:
            List of dictionaries with content, metadata, and distance
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            # Format results
            documents = []
            if results and 'documents' in results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {},
                        "distance": results['distances'][0][i] if 'distances' in results else 0.0
                    })

            logger.debug(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    def get_collection_count(self) -> int:
        """
        Get the number of documents in the collection

        Returns:
            Count of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0
