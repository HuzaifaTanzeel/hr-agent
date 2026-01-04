"""
HR Leave Management Agent
"""
import logging
from pydantic import BaseModel
from typing import List, Optional
from agents import Agent, AgentOutputSchema
from app.config.agent_config import AGENT_MODEL
from app.tools import (
    apply_for_leave,
    check_leave_balance,
    cancel_leave_request,
    get_leave_requests
)
from app.agent.guardrails import hr_input_guardrail, hr_output_guardrail

logger = logging.getLogger(__name__)


# ============================================================================
# OUTPUT SCHEMA
# ============================================================================

class LeaveAgentResponse(BaseModel):
    """Structured response from HR agent"""
    success: bool
    message: str


# ============================================================================
# AGENT DEFINITION
# ============================================================================

HR_AGENT_INSTRUCTIONS = """You are a helpful HR assistant for leave management.

**Your Capabilities:**
You can help employees with:
1. Applying for leave (annual, sick, casual, unpaid)
2. Checking leave balances
3. Viewing leave request history
4. Canceling pending leave requests
5. Answering questions about leave policies

**Important Guidelines:**
- Always be polite and professional
- Confirm details before applying for leave
- If dates are ambiguous (like "next week"), ask for specific dates
- When applying leave, ALWAYS ask for: leave type, start date, end date, and reason
- Use the tools to perform actions - don't make up information
- If a tool call fails, explain the error clearly to the user
- Suggest next steps when appropriate

**Date Format:**
- Always use YYYY-MM-DD format for dates
- If user says "next week", calculate the specific dates
- Today's date will be provided in context

**Leave Types:**
- ANNUAL: Annual leave / vacation
- SICK: Sick leave
- CASUAL: Casual leave
- UNPAID: Unpaid leave

**Example Interactions:**

User: "I need leave next week"
You: "I'd be happy to help you apply for leave. Could you please provide:
1. Which type of leave? (Annual/Sick/Casual/Unpaid)
2. Specific start and end dates
3. Reason for leave"

User: "Apply for annual leave from 2026-03-10 to 2026-03-14 for vacation"
You: [Call apply_for_leave tool, then confirm success]

User: "Check my balance"
You: [Call check_leave_balance tool, then present the information clearly]

Return your response in the LeaveAgentResponse format:
- success: true if the request was handled successfully
- message: Clear, friendly message for the user
"""


# Create HR Agent
hr_agent = Agent(
    name="HR Leave Agent",
    instructions=HR_AGENT_INSTRUCTIONS,
    model=AGENT_MODEL,
    tools=[
        apply_for_leave,
        check_leave_balance,
        cancel_leave_request,
        get_leave_requests
    ],
    output_type=AgentOutputSchema(LeaveAgentResponse, strict_json_schema=False),
    input_guardrails=[hr_input_guardrail],
    output_guardrails=[hr_output_guardrail],
)