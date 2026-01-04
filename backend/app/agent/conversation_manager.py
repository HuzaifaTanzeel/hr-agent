"""
Conversation Manager - Handles conversation sessions and persistence
"""
import uuid
import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ConversationInfo:
    """Information about a conversation session"""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.person_id: Optional[int] = None
        self.employee_id: Optional[int] = None
        self.status = ConversationStatus.ACTIVE
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.turn_count = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "person_id": self.person_id,
            "employee_id": self.employee_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "turn_count": self.turn_count
        }

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)
        self.turn_count += 1


class ConversationManager:
    """
    Manages conversation sessions for the HR agent.

    In production, this would be backed by a database (Conversation & Message tables).
    For now, we use in-memory storage.
    """

    def __init__(self):
        self._conversations: Dict[str, ConversationInfo] = {}
        self._lock = asyncio.Lock()

    async def create_conversation(
            self,
            person_id: int,
            employee_id: int
    ) -> ConversationInfo:
        """
        Create a new conversation session.

        Args:
            person_id: Person ID from the request
            employee_id: Employee ID from the request

        Returns:
            ConversationInfo object
        """
        async with self._lock:
            conversation_id = str(uuid.uuid4())
            conversation = ConversationInfo(conversation_id)
            conversation.person_id = person_id
            conversation.employee_id = employee_id

            self._conversations[conversation_id] = conversation

            logger.info(
                f"✅ Conversation created: {conversation_id} "
                f"(person_id={person_id}, employee_id={employee_id})"
            )

            return conversation

    async def get_conversation(
            self,
            conversation_id: str
    ) -> Optional[ConversationInfo]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            ConversationInfo or None if not found
        """
        async with self._lock:
            return self._conversations.get(conversation_id)

    async def update_activity(
            self,
            conversation_id: str
    ) -> bool:
        """
        Update conversation activity (called on each turn).

        Args:
            conversation_id: Conversation ID

        Returns:
            True if updated, False if conversation not found
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.update_activity()
                logger.debug(
                    f"📝 Conversation {conversation_id} activity updated "
                    f"(turn {conversation.turn_count})"
                )
                return True
            return False

    async def update_status(
            self,
            conversation_id: str,
            status: ConversationStatus
    ) -> bool:
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status

        Returns:
            True if updated, False if conversation not found
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.status = status
                logger.info(f"📊 Conversation {conversation_id} status: {status.value}")
                return True
            return False

    async def list_conversations(
            self,
            person_id: Optional[int] = None
    ) -> list:
        """
        List all conversations, optionally filtered by person_id.

        Args:
            person_id: Optional filter by person ID

        Returns:
            List of conversation dictionaries
        """
        async with self._lock:
            conversations = self._conversations.values()

            if person_id is not None:
                conversations = [
                    c for c in conversations
                    if c.person_id == person_id
                ]

            return [c.to_dict() for c in conversations]

    async def cleanup_old_conversations(
            self,
            hours: int = 24
    ) -> int:
        """
        Remove conversations older than specified hours.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of conversations removed
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            to_remove = []

            for conv_id, conv in self._conversations.items():
                age = (now - conv.last_activity).total_seconds() / 3600
                if age > hours:
                    to_remove.append(conv_id)

            for conv_id in to_remove:
                del self._conversations[conv_id]

            if to_remove:
                logger.info(f"🧹 Cleaned up {len(to_remove)} old conversations")

            return len(to_remove)


# Global instance
conversation_manager = ConversationManager()