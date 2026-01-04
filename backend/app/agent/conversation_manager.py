"""
Conversation Manager - Handles conversation sessions and persistence
"""
import uuid
import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.conversation_repository import (
    ConversationRepository,
    MessageRepository
)

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
    
    Now backed by database (Conversation & Message tables).
    """

    def __init__(self):
        self._lock = asyncio.Lock()

    async def create_conversation(
            self,
            db: AsyncSession,
            employee_id: int
    ) -> ConversationInfo:
        """
        Create a new conversation session in database.

        Args:
            db: Database session
            employee_id: Employee ID from the request

        Returns:
            ConversationInfo object
        """
        async with self._lock:
            conversation_id = str(uuid.uuid4())
            
            # Create in database
            db_conversation = await ConversationRepository.create(
                db=db,
                conversation_id=conversation_id,
                employee_id=employee_id
            )
            
            # Create ConversationInfo from database model
            conversation = ConversationInfo(conversation_id)
            conversation.employee_id = employee_id
            # person_id is same as employee_id (employee has unique person_id FK)
            conversation.person_id = employee_id  # For backward compatibility in ConversationInfo
            conversation.created_at = db_conversation.started_at
            conversation.last_activity = db_conversation.last_activity
            conversation.turn_count = db_conversation.turn_count

            logger.info(
                f"✅ Conversation created: {conversation_id} "
                f"(employee_id={employee_id})"
            )

            return conversation

    async def get_conversation(
            self,
            db: AsyncSession,
            conversation_id: str
    ) -> Optional[ConversationInfo]:
        """
        Get conversation by ID from database.

        Args:
            db: Database session
            conversation_id: Conversation ID (UUID string)

        Returns:
            ConversationInfo or None if not found
        """
        async with self._lock:
            db_conversation = await ConversationRepository.get_by_conversation_id(db, conversation_id)
            
            if not db_conversation:
                return None
            
            # Convert to ConversationInfo
            conversation = ConversationInfo(db_conversation.conversation_id)
            conversation.employee_id = db_conversation.employee_id
            conversation.person_id = db_conversation.employee_id  # Same as employee_id for compatibility
            conversation.status = ConversationStatus(db_conversation.status)
            conversation.created_at = db_conversation.started_at
            conversation.last_activity = db_conversation.last_activity
            conversation.turn_count = db_conversation.turn_count
            
            return conversation

    async def update_activity(
            self,
            db: AsyncSession,
            conversation_id: str
    ) -> bool:
        """
        Update conversation activity (called on each turn).

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            True if updated, False if conversation not found
        """
        async with self._lock:
            success = await ConversationRepository.update_activity(db, conversation_id)
            if success:
                logger.debug(f"📝 Conversation {conversation_id} activity updated")
            return success

    async def update_status(
            self,
            db: AsyncSession,
            conversation_id: str,
            status: ConversationStatus
    ) -> bool:
        """
        Update conversation status.

        Args:
            db: Database session
            conversation_id: Conversation ID
            status: New status

        Returns:
            True if updated, False if conversation not found
        """
        async with self._lock:
            success = await ConversationRepository.update_status(db, conversation_id, status.value)
            if success:
                logger.info(f"📊 Conversation {conversation_id} status: {status.value}")
            return success

    async def list_conversations(
            self,
            db: AsyncSession,
            employee_id: Optional[int] = None
    ) -> list:
        """
        List all conversations, optionally filtered by employee_id.

        Args:
            db: Database session
            employee_id: Optional filter by employee ID

        Returns:
            List of conversation dictionaries
        """
        async with self._lock:
            if employee_id is not None:
                db_conversations = await ConversationRepository.get_by_employee_id(db, employee_id)
            else:
                # Get all - would need a new method, for now return empty
                db_conversations = []

            # Convert to dict format
            conversations = []
            for conv in db_conversations:
                conversations.append({
                    "conversation_id": conv.conversation_id,
                    "employee_id": conv.employee_id,
                    "person_id": conv.employee_id,  # Same as employee_id for compatibility
                    "status": conv.status,
                    "created_at": conv.started_at.isoformat() if conv.started_at else None,
                    "last_activity": conv.last_activity.isoformat() if conv.last_activity else None,
                    "turn_count": conv.turn_count
                })

            return conversations

    async def save_message(
            self,
            db: AsyncSession,
            conversation_id: str,
            sender_type: str,
            content: str,
            intent: Optional[str] = None
    ) -> bool:
        """
        Save a message to the database.

        Args:
            db: Database session
            conversation_id: Conversation ID (UUID string)
            sender_type: 'USER' or 'ASSISTANT'
            content: Message content
            intent: Optional intent classification

        Returns:
            True if saved, False if conversation not found
        """
        async with self._lock:
            # Verify conversation exists
            db_conv = await ConversationRepository.get_by_conversation_id(db, conversation_id)
            if not db_conv:
                logger.error(f"❌ Conversation {conversation_id} not found for message")
                return False
            
            # Save message (conversation_id is now the UUID string, which is the primary key)
            await MessageRepository.create(
                db=db,
                conversation_id=conversation_id,  # Use UUID string directly (primary key)
                sender_type=sender_type,
                content=content,
                intent=intent
            )
            
            logger.debug(f"💬 Message saved to conversation {conversation_id}")
            return True

    async def get_messages(
            self,
            db: AsyncSession,
            conversation_id: str
    ) -> list:
        """
        Get all messages for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID (UUID string)

        Returns:
            List of message dictionaries
        """
        messages = await MessageRepository.get_by_conversation_uuid(db, conversation_id)
        
        return [
            {
                "id": msg.id,
                "sender_type": msg.sender_type,
                "content": msg.content,
                "intent": msg.intent,
                "sequence_number": msg.sequence_number,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]

    async def cleanup_old_conversations(
            self,
            db: AsyncSession,
            hours: int = 24
    ) -> int:
        """
        Mark old conversations as CLOSED (soft delete).

        Args:
            db: Database session
            hours: Age threshold in hours

        Returns:
            Number of conversations closed
        """
        # This would require a query to find old conversations
        # For now, return 0 - can be implemented later
        logger.info("🧹 Cleanup old conversations - not yet implemented")
        return 0


# Global instance
conversation_manager = ConversationManager()