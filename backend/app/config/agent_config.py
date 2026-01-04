"""
Agent Configuration - LLM models and settings
"""
import os

from dotenv import load_dotenv
load_dotenv()
# LLM Models
# Agent accepts model as a string (e.g., "openai/gpt-4o-mini") or Model instance
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-5")
GUARDRAIL_MODEL = os.getenv("GUARDRAIL_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent Settings
MAX_TURNS = 5  # Maximum conversation turns per request

