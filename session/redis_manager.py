from redis.asyncio import Redis
import json
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class RedisSessionManager:
    """Thread-safe session management with Redis"""

    def __init__(self, redis_client: Redis, ttl: int = 3600):
        """
        Initialize Redis session manager

        Args:
            redis_client: Async Redis client instance
            ttl: Session time-to-live in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.ttl = ttl

    async def create_session(self, call_sid: str, session_data: dict):
        """
        Create new session

        Args:
            call_sid: Twilio call SID
            session_data: Session data dictionary
        """
        try:
            # Initialize conversation history as empty list
            session_data['conversation_history'] = json.dumps([])

            # Store in Redis
            await self.redis.hset(f"session:{call_sid}", mapping=session_data)
            await self.redis.expire(f"session:{call_sid}", self.ttl)

            logger.info(f"Created session for call {call_sid}")
        except Exception as e:
            logger.error(f"Error creating session for {call_sid}: {e}")
            raise

    async def get_session(self, call_sid: str) -> Optional[Dict]:
        """
        Get session data

        Args:
            call_sid: Twilio call SID

        Returns:
            Session data dictionary or None if not found
        """
        try:
            data = await self.redis.hgetall(f"session:{call_sid}")
            if not data:
                logger.warning(f"Session not found for call {call_sid}")
                return None

            # Deserialize conversation history
            if 'conversation_history' in data:
                try:
                    data['conversation_history'] = json.loads(data['conversation_history'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode conversation history for {call_sid}")
                    data['conversation_history'] = []

            return data
        except Exception as e:
            logger.error(f"Error getting session for {call_sid}: {e}")
            return None

    async def update_session(self, call_sid: str, updates: dict):
        """
        Update session data

        Args:
            call_sid: Twilio call SID
            updates: Dictionary of fields to update
        """
        try:
            # Serialize complex types
            serialized_updates = {}
            for key, value in updates.items():
                if isinstance(value, (list, dict)):
                    serialized_updates[key] = json.dumps(value)
                else:
                    serialized_updates[key] = str(value)

            await self.redis.hset(f"session:{call_sid}", mapping=serialized_updates)
            await self.redis.expire(f"session:{call_sid}", self.ttl)

            logger.debug(f"Updated session for call {call_sid}")
        except Exception as e:
            logger.error(f"Error updating session for {call_sid}: {e}")
            raise

    async def add_message(self, call_sid: str, message: dict):
        """
        Add message to conversation history (thread-safe)

        Uses Redis lock to prevent race conditions when multiple
        requests try to add messages simultaneously.

        Args:
            call_sid: Twilio call SID
            message: Message dictionary with role, content, timestamp
        """
        lock_key = f"lock:session:{call_sid}"

        try:
            # Acquire distributed lock
            async with self.redis.lock(lock_key, timeout=5):
                session = await self.get_session(call_sid)
                if not session:
                    logger.warning(f"Cannot add message - session not found for {call_sid}")
                    return

                history = session.get('conversation_history', [])
                history.append(message)

                # Update conversation history
                await self.redis.hset(
                    f"session:{call_sid}",
                    "conversation_history",
                    json.dumps(history)
                )
                await self.redis.expire(f"session:{call_sid}", self.ttl)

                logger.debug(f"Added message to session {call_sid}, history length: {len(history)}")
        except Exception as e:
            logger.error(f"Error adding message to session {call_sid}: {e}")
            raise

    async def delete_session(self, call_sid: str):
        """
        Clean up session

        Args:
            call_sid: Twilio call SID
        """
        try:
            result = await self.redis.delete(f"session:{call_sid}")
            if result:
                logger.info(f"Deleted session for call {call_sid}")
            else:
                logger.warning(f"Session not found for deletion: {call_sid}")
        except Exception as e:
            logger.error(f"Error deleting session {call_sid}: {e}")

    async def get_all_sessions(self) -> Dict[str, dict]:
        """
        Get all active sessions

        Returns:
            Dictionary mapping call_sid to session data
        """
        sessions = {}
        try:
            async for key in self.redis.scan_iter("session:*"):
                call_sid = key.replace("session:", "")
                session = await self.get_session(call_sid)
                if session:
                    sessions[call_sid] = session
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")

        return sessions

    async def session_exists(self, call_sid: str) -> bool:
        """
        Check if session exists

        Args:
            call_sid: Twilio call SID

        Returns:
            True if session exists, False otherwise
        """
        try:
            return await self.redis.exists(f"session:{call_sid}") > 0
        except Exception as e:
            logger.error(f"Error checking session existence for {call_sid}: {e}")
            return False
