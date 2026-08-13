"""Google ADK Agent Definition and Export."""

from google.adk.agents import Agent
from ..config import settings
from .prompt import SYSTEM_INSTRUCTION
from .tools import ALL_TOOLS

# Formatted default system instruction
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
