"""
Agent API Routes - REST endpoints for HR Agent
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.session import get_db
from app.agent.runner import run_hr_agent, end_conversation
from app.agent.conversation_manager import conversation_manager

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class ChatRequest(BaseModel):
    """Request to chat with HR agent"""
    message: str = Field(..., min_length=1, max_length=2000)
    employee_id: int = Field(..., gt=0)
    person_id: int = Field(..., gt=0)
    conversation_id: Optional[str] = Field(None, description="Optional - for continuing conversation")


class ChatResponse(BaseModel):
    """Response from HR agent"""
    conversation_id: str
    success: bool
    message: str
    intent: str
    turn: int


class ConversationListResponse(BaseModel):
    """List of conversations"""
    conversations: List[dict]
    total: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with HR Agent",
    description="Send a message to the HR agent and get a response"
)
async def chat_with_agent(
        request: ChatRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Chat with the HR agent.

    **First message:** Don't include conversation_id
    **Subsequent messages:** Include the conversation_id from previous response

    Example:
    ```json
    {
        "message": "I need 3 days leave next week",
        "employee_id": 1,
        "person_id": 1,
        "conversation_id": "abc-123"  // Optional
    }
    ```
    """
    try:
        logger.info(f"📨 Received chat request - Employee: {request.employee_id}, Person: {request.person_id}")
        logger.info(f"   Message: {request.message[:100]}...")
        logger.info(f"   Conversation ID: {request.conversation_id or 'NEW'}")
        
        # Run agent
        result = await run_hr_agent(
            message=request.message,
            employee_id=request.employee_id,
            person_id=request.person_id,
            conversation_id=request.conversation_id,
            db=db
        )

        logger.info(f"✅ Chat request completed - Conversation: {result.get('conversation_id')}")
        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"❌ Error in chat_with_agent: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.post(
    "/conversations/{conversation_id}/end",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="End conversation",
    description="Mark a conversation as completed"
)
async def end_conversation_endpoint(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    End a conversation session.

    This marks the conversation as completed. No more messages can be sent
    in this conversation after calling this endpoint.
    """
    success = await end_conversation(db, conversation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="Get all conversations, optionally filtered by employee_id"
)
async def list_conversations(
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversations.

    Optionally filter by employee_id to get conversations for a specific employee.
    """
    conversations = await conversation_manager.list_conversations(
        db=db,
        employee_id=employee_id
    )

    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations)
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=dict,
    summary="Get conversation details",
    description="Get details of a specific conversation"
)
async def get_conversation_details(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific conversation"""
    conversation = await conversation_manager.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    return conversation.to_dict()


@router.delete(
    "/conversations/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Cleanup old conversations",
    description="Remove conversations older than specified hours"
)
async def cleanup_conversations(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    Cleanup old conversations.

    Removes conversations that haven't had activity for the specified number of hours.
    Default: 24 hours
    """
    count = await conversation_manager.cleanup_old_conversations(db=db, hours=hours)

    return {
        "message": f"Cleaned up {count} old conversations",
        "removed": count
    }


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[dict],
    summary="Get conversation messages",
    description="Get all messages for a specific conversation in sequence"
)
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all messages for a conversation.
    
    Messages are returned in sequence order (by sequence_number and created_at).
    """
    messages = await conversation_manager.get_messages(db, conversation_id)
    
    if not messages:
        # Check if conversation exists
        conversation = await conversation_manager.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
    
    return messages


@router.get(
    "/employees/{employee_id}/conversations",
    response_model=ConversationListResponse,
    summary="Get employee conversations",
    description="Get all conversations for a specific employee"
)
async def get_employee_conversations(
    employee_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all conversations for an employee.
    
    Returns conversations ordered by last activity (most recent first).
    """
    conversations = await conversation_manager.list_conversations(
        db=db,
        employee_id=employee_id
    )
    
    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations)
    )