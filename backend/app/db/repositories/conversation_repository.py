"""
Repository for Conversation and Message operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime, timezone

from app.db.models.models import Conversation, Message


class ConversationRepository:
    """Repository for Conversation operations"""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: str,
        employee_id: int
    ) -> Conversation:
        """Create a new conversation with conversation_id as primary key"""
        conversation = Conversation(
            conversation_id=conversation_id,
            employee_id=employee_id,
            status="ACTIVE",
            turn_count=0
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
    
    @staticmethod
    async def get_by_conversation_id(
        db: AsyncSession,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Get conversation by conversation_id (UUID string - primary key)"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()
    
    
    @staticmethod
    async def get_by_employee_id(
        db: AsyncSession,
        employee_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """Get all conversations for an employee"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.employee_id == employee_id)
            .order_by(desc(Conversation.last_activity))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    
    @staticmethod
    async def update_activity(
        db: AsyncSession,
        conversation_id: str
    ) -> bool:
        """Update last activity and increment turn count"""
        conversation = await ConversationRepository.get_by_conversation_id(db, conversation_id)
        if conversation:
            conversation.last_activity = datetime.now(timezone.utc)
            conversation.turn_count += 1
            await db.commit()
            await db.refresh(conversation)
            return True
        return False
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        conversation_id: str,
        status: str
    ) -> bool:
        """Update conversation status"""
        conversation = await ConversationRepository.get_by_conversation_id(db, conversation_id)
        if conversation:
            conversation.status = status
            await db.commit()
            await db.refresh(conversation)
            return True
        return False


class MessageRepository:
    """Repository for Message operations"""
    
    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: str,  # UUID string (primary key of conversation)
        sender_type: str,
        content: str,
        intent: Optional[str] = None,
        sequence_number: Optional[int] = None
    ) -> Message:
        """Create a new message"""
        # If sequence_number not provided, get the next one
        if sequence_number is None:
            last_message = await MessageRepository.get_last_message(db, conversation_id)
            sequence_number = (last_message.sequence_number + 1) if last_message else 1
        
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
            intent=intent,
            sequence_number=sequence_number
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
    
    @staticmethod
    async def get_by_conversation_id(
        db: AsyncSession,
        conversation_id: str,  # UUID string (primary key)
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Get all messages for a conversation, ordered by sequence"""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number, Message.created_at)
        )
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_last_message(
        db: AsyncSession,
        conversation_id: str  # UUID string
    ) -> Optional[Message]:
        """Get the last message in a conversation (highest sequence_number)"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.sequence_number))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_conversation_uuid(
        db: AsyncSession,
        conversation_uuid: str
    ) -> List[Message]:
        """Get all messages for a conversation by UUID string (alias for get_by_conversation_id)"""
        return await MessageRepository.get_by_conversation_id(db, conversation_uuid)

