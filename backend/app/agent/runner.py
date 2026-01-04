"""
Agent Runner - Orchestrates agent execution with conversation management
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from agents import Runner
from agents.memory import SQLiteSession
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.hr_agent import hr_agent
from app.agent.intent_classifier import classify_intent
from app.agent.conversation_manager import conversation_manager, ConversationStatus
from app.config.agent_config import MAX_TURNS
from app.rag.rag_manager import rag_manager

logger = logging.getLogger(__name__)


async def run_hr_agent(
        message: str,
        employee_id: int,
        person_id: int,
        conversation_id: Optional[str],
        db: AsyncSession
) -> Dict[str, Any]:

    """
    Run the HR agent with conversation management.

    Flow:
    1. Create or retrieve conversation
    2. Classify intent (determines if tools needed)
    3. Run agent with appropriate context
    4. Update conversation state
    5. Return response with conversation_id

    Args:
        message: User's message
        employee_id: Employee ID (injected into context)
        person_id: Person ID
        conversation_id: Optional - existing conversation ID
        db: Database session for tools

    Returns:
        Dictionary with response and conversation_id
    """

    logger.info("="*60)
    logger.info("▶️  HR AGENT EXECUTION START")
    logger.info(f"   Employee: {employee_id}")
    logger.info(f"   Person: {person_id}")
    logger.info(f"   Conversation: {conversation_id or 'NEW'}")
    logger.info(f"   Message: {message[:100]}...")

    try:
        # Step 1: Get or create conversation
        if conversation_id:
            conversation = await conversation_manager.get_conversation(db, conversation_id)
            if not conversation:
                logger.warning(f"   ⚠️  Conversation {conversation_id} not found, creating new")
                conversation = await conversation_manager.create_conversation(
                    db=db,
                    employee_id=employee_id
                )
        else:
            conversation = await conversation_manager.create_conversation(
                db=db,
                employee_id=employee_id
            )
        
        # Save user message to database
        await conversation_manager.save_message(
            db=db,
            conversation_id=conversation.conversation_id,
            sender_type="USER",
            content=message
        )

        # Step 2: Classify intent
        intent = await classify_intent(message)

        # Step 3: Retrieve policy context if this is a policy question
        policy_context = ""
        if intent == "POLICY_QUESTION":
            try:
                retrieval_service = rag_manager.get_retrieval_service()
                chunks = retrieval_service.retrieve(query=message, top_k=3)
                
                if chunks:
                    policy_context = retrieval_service.format_context(chunks)
                    logger.info(f"📚 Retrieved {len(chunks)} policy chunks for context")
                else:
                    logger.warning("⚠️  No policy chunks retrieved")
                    policy_context = "No relevant policy information found in the knowledge base."
            except Exception as e:
                logger.error(f"❌ Error retrieving policy context: {str(e)}")
                policy_context = "Unable to retrieve policy information at this time."

        # Step 4: Prepare agent context
        # Add current date and employee context to the message
        if policy_context:
            context_message = f"""[Context]
- Date: {datetime.now().strftime('%Y-%m-%d')}
- Employee ID: {employee_id}
- Person ID: {person_id}

[Relevant Policy Information]
{policy_context}

[User Message]
{message}
"""
        else:
            context_message = f"""[Context]
- Date: {datetime.now().strftime('%Y-%m-%d')}
- Employee ID: {employee_id}
- Person ID: {person_id}

[User Message]
{message}
"""

        # Step 5: Setup memory session
        # This maintains context across turns within the conversation
        session = SQLiteSession(session_id=conversation.conversation_id)

        # Step 6: Inject database session into agent context
        # The tools need this to access the database
        # We'll pass it via the context
        agent_context = {
            "db": db,
            "employee_id": employee_id,
            "person_id": person_id,
            "intent": intent
        }

        logger.info(f"🤖 Running agent (intent: {intent})...")

        # Step 7: Run agent
        result = await Runner.run(
            hr_agent,
            context_message,
            session=session,
            max_turns=MAX_TURNS,
            context=agent_context  # Pass db and context
        )

        # Step 8: Extract response
        response = result.final_output

        # Step 9: Save assistant response to database
        await conversation_manager.save_message(
            db=db,
            conversation_id=conversation.conversation_id,
            sender_type="ASSISTANT",
            content=response.message,
            intent=intent
        )

        # Step 10: Update conversation activity
        await conversation_manager.update_activity(db, conversation.conversation_id)

        logger.info(f"✅ Agent execution completed successfully")
        logger.info(f"   Success: {response.success}")
        logger.info(f"   Message: {response.message[:100]}...")
        logger.info("="*60)

        # Step 11: Return structured response
        return {
            "conversation_id": conversation.conversation_id,
            "success": response.success,
            "message": response.message,
            "intent": intent,
            "turn": conversation.turn_count
        }

    except Exception as e:
        logger.error(f"❌ Agent execution failed: {type(e).__name__}: {str(e)}", exc_info=True)
        logger.error("="*60)

        # Ensure we have a conversation for error response
        error_conversation_id = conversation_id or f"error-{int(datetime.now().timestamp() * 1000)}"
        error_turn = 0
        
        try:
            if conversation_id:
                conversation = await conversation_manager.get_conversation(db, conversation_id)
                if conversation:
                    await conversation_manager.update_status(
                        db,
                        conversation_id,
                        ConversationStatus.FAILED
                    )
                    error_turn = conversation.turn_count
            else:
                # Create a conversation for error tracking
                try:
                    error_conversation = await conversation_manager.create_conversation(
                        db=db,
                        employee_id=employee_id
                    )
                    error_conversation_id = error_conversation.conversation_id
                    await conversation_manager.update_status(
                        db,
                        error_conversation_id,
                        ConversationStatus.FAILED
                    )
                except Exception as create_error:
                    logger.error(f"Failed to create error conversation: {create_error}")
                    # Fallback: generate a temporary ID (already set above)
                    pass
        except Exception as handler_error:
            logger.error(f"Error in error handler: {handler_error}")
            # Use the fallback ID already set

        # Return error response with required fields - ensure conversation_id is always a string
        return {
            "conversation_id": str(error_conversation_id),
            "success": False,
            "message": "I encountered an error while processing your request. Please try again.",
            "intent": "error",
            "turn": error_turn
        }


async def end_conversation(db: AsyncSession, conversation_id: str) -> bool:
    """
    Mark a conversation as completed.

    Args:
        db: Database session
        conversation_id: Conversation ID to end

    Returns:
        True if successful, False if conversation not found
    """
    logger.info(f"🏁 Ending conversation: {conversation_id}")
    success = await conversation_manager.update_status(
        db,
        conversation_id,
        ConversationStatus.COMPLETED
    )
    return success