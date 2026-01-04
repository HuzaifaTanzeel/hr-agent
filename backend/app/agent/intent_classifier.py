"""
Intent Classifier - Classifies user queries into Policy Question, HR Request, or None
"""
import logging
from pydantic import BaseModel
from agents import Agent, AgentOutputSchema, Runner
from app.config.agent_config import AGENT_MODEL

logger = logging.getLogger(__name__)


# ============================================================================
# INTENT CLASSIFICATION OUTPUT (STRICT)
# ============================================================================

class IntentClassification(BaseModel):
    """
    STRICT intent classification result.
    Allowed values only:
    - POLICY_QUESTION
    - HR_REQUEST
    - NONE
    """
    intent: str

INTENT_CLASSIFIER_INSTRUCTIONS = """
You are an intent classifier for an HR AI Agent system.

Your task is to classify the user's message into EXACTLY ONE of the following values:

- POLICY_QUESTION
- HR_REQUEST
- NONE

Return ONLY ONE of these values.
Do NOT return explanations, confidence, or extra text.

Definitions:

1. POLICY_QUESTION
- User is asking about HR policies, rules, or general information
- Examples:
  - "What is the work from home policy?"
  - "How many annual leaves do I get?"
  - "What is the sick leave policy?"

2. HR_REQUEST
- User wants to perform an action
- Examples:
  - "Apply for annual leave from Jan 1 to Jan 2"
  - "Check my leave balance"
  - "Cancel my leave request"
  - "Show my leave history"

3. NONE
- Greetings, small talk, or irrelevant messages
- Examples:
  - "Hi"
  - "Hello"
  - "Thanks"
  - "How are you?"
  - Random or unrelated input

Rules:
- If the message asks for information → POLICY_QUESTION
- If the message asks for an action → HR_REQUEST
- If no HR meaning exists → NONE

Output format:
Return ONLY one string from:
POLICY_QUESTION | HR_REQUEST | NONE
"""

intent_classifier_agent = Agent(
    name="Intent Classifier",
    instructions=INTENT_CLASSIFIER_INSTRUCTIONS,
    model=AGENT_MODEL,
    output_type=AgentOutputSchema(
        IntentClassification,
        strict_json_schema=True  # Enforces clean output
    ),
)


# ============================================================================
# CLASSIFICATION FUNCTION
# ============================================================================

async def classify_intent(message: str) -> str:
    """
    Classify user message intent.

    Returns:
        One of: POLICY_QUESTION | HR_REQUEST | NONE
    """
    logger.info(f"🔍 Classifying intent for message: {message[:100]}")

    try:
        result = await Runner.run(
            intent_classifier_agent,
            message,
            max_turns=1
        )

        intent = result.final_output.intent

        if intent not in {"POLICY_QUESTION", "HR_REQUEST", "NONE"}:
            logger.warning(f"⚠️ Invalid intent returned: {intent}")
            return "NONE"

        logger.info(f"✅ Intent classified as: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent classification failed: {str(e)}")
        return "NONE"
