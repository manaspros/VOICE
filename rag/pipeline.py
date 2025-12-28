from .retriever import RAGRetriever
from .generator import GeminiGenerator
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline orchestrator"""

    def __init__(self, retriever: RAGRetriever, generator: GeminiGenerator):
        """
        Initialize RAG pipeline

        Args:
            retriever: RAG retriever instance
            generator: Gemini generator instance
        """
        self.retriever = retriever
        self.generator = generator
        logger.info("RAG pipeline initialized")

    async def process_query(
        self,
        user_query: str,
        conversation_history: List[Dict],
        language: str = "en",
        n_results: int = 5
    ) -> str:
        """
        Process query end-to-end with RAG

        Args:
            user_query: User's query text
            conversation_history: Previous conversation messages
            language: Language code (en or hi-IN)
            n_results: Number of documents to retrieve

        Returns:
            Generated response text
        """
        try:
            logger.debug(f"Processing query: {user_query[:50]}...")

            # Step 1: Retrieve relevant documents
            retrieved_docs = await self.retriever.retrieve(
                query=user_query,
                n_results=n_results
            )

            logger.debug(f"Retrieved {len(retrieved_docs)} documents")

            # Step 2: Generate response with context
            response = await self.generator.generate_response(
                user_query=user_query,
                retrieved_docs=retrieved_docs,
                conversation_history=conversation_history,
                language=language
            )

            return response

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            # Return fallback response
            fallback = {
                "en": "I'm sorry, I'm having trouble processing your request. Please try again.",
                "hi-IN": "क्षमा करें, मुझे आपका अनुरोध संसाधित करने में समस्या हो रही है। कृपया पुनः प्रयास करें।"
            }
            return fallback.get(language, fallback["en"])
