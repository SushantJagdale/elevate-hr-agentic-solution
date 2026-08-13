"""ADK Agent Definition for ADK Web UI & Runner."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from google.adk.agents import Agent
from app.config import settings
from app.agent.prompt import SYSTEM_INSTRUCTION
from app.agent.tools import ALL_TOOLS

# Formatted default system instruction for Alex Chen (E1209)
default_instruction = SYSTEM_INSTRUCTION.format(
    user_id="E1209",
    user_name="Alex Chen",
    department="Engineering",
    role="Senior Software Engineer",
    work_location_type="Remote",
)

# Root ADK Agent Export
root_agent = Agent(
    name="enterprise_hr_assistant",
    model=settings.GEMINI_MODEL,
    instruction=default_instruction,
    description="Enterprise HR Virtual Assistant providing grounded policy Q&A, leave management, IT ticketing, and cross-system workflows.",
    tools=ALL_TOOLS,
)
