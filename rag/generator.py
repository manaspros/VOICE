import google.generativeai as genai
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class GeminiGenerator:
    """Generate responses using Google Gemini LLM"""

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialize Gemini generator

        Args:
            api_key: Google Gemini API key
            model_name: Model name to use (default: gemini-pro)
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Gemini generator with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            raise

    async def generate_response(
        self,
        user_query: str,
        retrieved_docs: List[Dict],
        conversation_history: List[Dict],
        language: str = "en"
    ) -> str:
        """
        Generate response with RAG context

        Args:
            user_query: User's query text
            retrieved_docs: Documents retrieved from vector DB
            conversation_history: Previous conversation messages
            language: Language code (en or hi-IN)

        Returns:
            Generated response text
        """
        try:
            # Build context from retrieved documents
            context = self._build_context(retrieved_docs)

            # Format conversation history (last 5 messages)
            history = self._format_history(conversation_history)

            # Create prompt
            prompt = self._create_prompt(user_query, context, history, language)

            # Generate response
            response = await self.model.generate_content_async(prompt)

            if response and response.text:
                logger.debug(f"Generated response for query: {user_query[:50]}...")
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return self._fallback_response(language)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_response(language)

    def _build_context(self, docs: List[Dict]) -> str:
        """
        Build context string from retrieved documents

        Args:
            docs: List of document dictionaries

        Returns:
            Formatted context string
        """
        if not docs:
            return "No relevant context found."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"{i}. {doc['content']}")

        return "\n".join(context_parts)

    def _format_history(self, history: List[Dict]) -> str:
        """
        Format conversation history

        Args:
            history: List of conversation messages

        Returns:
            Formatted history string
        """
        if not history:
            return "No previous conversation."

        formatted = []
        # Get last 5 messages
        for msg in history[-5:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            formatted.append(f"{role.capitalize()}: {content}")

        return "\n".join(formatted)

    def _create_prompt(
        self,
        query: str,
        context: str,
        history: str,
        language: str
    ) -> str:
        """
        Create RAG prompt for Gemini

        Args:
            query: User query
            context: Retrieved context
            history: Conversation history
            language: Language code

        Returns:
            Complete prompt string
        """
        lang_instruction = {
            "en": "Respond in English",
            "hi-IN": "Respond in Hindi (Devanagari script)"
        }.get(language, "Respond in English")

        prompt = f"""You are a helpful AI assistant for a company's voice support system.

Context from knowledge base:
{context}

Conversation history:
{history}

User query: {query}

Instructions:
1. Answer based on the context provided above
2. If the answer is not in the context, politely say you don't know
3. Be concise and helpful (2-3 sentences maximum for voice)
4. {lang_instruction}
5. Do not mention that you're reading from a knowledge base
6. Sound natural and conversational

Response:"""

        return prompt

    def _fallback_response(self, language: str) -> str:
        """
        Fallback response when API fails

        Args:
            language: Language code

        Returns:
            Fallback message
        """
        fallbacks = {
            "en": "I apologize, I'm having trouble processing your request right now. Please try again in a moment.",
            "hi-IN": "क्षमा करें, मुझे आपका अनुरोध संसाधित करने में समस्या हो रही है। कृपया कुछ समय बाद पुनः प्रयास करें।"
        }
        return fallbacks.get(language, fallbacks["en"])
