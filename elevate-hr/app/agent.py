# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import re
from zoneinfo import ZoneInfo

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.genai import types

MODEL = "gemini-3.6-flash"
MCP_TOKEN = os.getenv("MCP_TOKEN", "mcp_rM5ndDaEvTXihkeYiCX5f_TU8jOAaqEDp9lktkXiKnc")

def load_endpoints_from_spec():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec_path = os.path.join(base_dir, "moc.json")
    try:
        with open(spec_path, "r") as f:
            data = json.load(f)
            desc = data.get("info", {}).get("description", "")
            ww_match = re.search(r"https://[a-zA-Z0-9.-]+/work-week/mcp/?", desc)
            si_match = re.search(r"https://[a-zA-Z0-9.-]+/service-immediately/mcp/?", desc)
            if ww_match and si_match:
                return ww_match.group(0), si_match.group(0)
    except Exception as e:
        print("Warning: Failed to load custom endpoints from moc.json, falling back to defaults.", e)
    return (
        "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/",
        "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/"
    )

WORKWEEK_URL, SERVICEIMMEDIATELY_URL = load_endpoints_from_spec()

# 1. Connect to the WorkWeek MCP server
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=WORKWEEK_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# 2. Connect to the ServiceImmediately MCP server
serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=SERVICEIMMEDIATELY_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# 3. Define Orchestrator shared tools
def query_policy_knowledge_base(query: str) -> str:
    """Queries the corporate policy document database to retrieve policy details.
    
    Args:
        query: The search term or policy question (e.g. "bereavement leave policy" or "remote work monitor eligibility").
        
    Returns:
        A grounded snippet from the policy document containing details and section citations.
    """
    q = query.lower()
    if "bereavement" in q:
        return (
            "Employees are eligible for up to 5 days of paid bereavement leave. "
            "[Source: Leave Policy 2026, Section 4.2](https://hr.corp/policies/leave#sec4.2)"
        )
    elif "monitor" in q or "hardware" in q or "equipment" in q or "remote work" in q:
        return (
            "Remote employees (>80% WFH) are eligible for 1x 27-inch 4K monitor. "
            "[Source: Remote Work Equipment Policy 2026, Section 2.1](https://hr.corp/policies/equipment#sec2.1)"
        )
    return "I am sorry, but official policy records do not contain sufficient information regarding this request."

async def resolve_employee_id() -> str:
    """Resolves the current authenticated user session's corporate employee ID.
    
    Returns:
        The employee ID string (e.g. 'EMP-336').
    """
    headers = {"X-MCP-Token": MCP_TOKEN}
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            async with streamable_http_client(WORKWEEK_URL, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    res = await session.call_tool("get_current_employee_id", {})
                    if hasattr(res, "content"):
                        for item in res.content:
                            if hasattr(item, "text"):
                                return item.text.strip()
                    return str(res).strip()
    except Exception as e:
        print("Warning: Failed to resolve employee ID dynamically, falling back to EMP-336.", e)
    return "EMP-336"

# 4. Construct WorkWeek worker subagent
workweek_worker = Agent(
    name="workweek_worker",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Handles employee profile updates, vacation and sick leave requests, remaining leave balances, and cancellations on the WorkWeek system.",
    instruction=(
        "You are the specialized WorkWeek worker agent.\n"
        "You manage employee profile context and leave workflows.\n"
        "For any request involving leave management, fetching personal contact details/address, or personal contact info updates:\n"
        "1. Check if the caller/orchestrator has provided the employee ID in the conversation. If not, ask the user or the orchestrator.\n"
        "2. If requested to retrieve personal contact details or shipping address, call `get_personal_info` and return the address and phone number details.\n"
        "3. If requesting leave, fetch the leave balances first using `get_employee_balances`.\n"
        "4. Validate that the start and end dates are chronological (start_date <= end_date) and the employee has sufficient vacation remaining.\n"
        "5. If valid, request time off using `request_time_off` and output the reference ID and status.\n"
        "6. If requested, check leave history using `get_leave_requests` or cancel pending leave using `cancel_leave_request`."
    ),
    tools=[workweek_mcp],
)

# 5. Construct ServiceImmediately worker subagent
itsm_worker = Agent(
    name="itsm_worker",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Handles IT incident tickets, support tickets, checking ticket lists, adding timeline comments, and ticket status updates on the ServiceImmediately system.",
    instruction=(
        "You are the specialized ServiceImmediately IT support agent.\n"
        "You manage support tickets and incident reports.\n"
        "For any request involving support ticket creation, comment updates, or status queries:\n"
        "1. Check if the caller/orchestrator has provided the employee ID. If not, ask for it.\n"
        "2. Classify the priority (priority='1 - Critical' requires outage, crash, or system downtime keywords in the description).\n"
        "3. Fetch active tickets using `list_tickets` to check for duplicates in the same category within the last 24 hours (prevent duplication).\n"
        "4. If no duplicate exists, create the ticket using `create_ticket` and output the incident number and state.\n"
        "5. If requested, update a ticket status using `update_ticket_status` or add timeline comments with `add_ticket_comment`."
    ),
    tools=[serviceimmediately_mcp],
)

# 6. Construct Master Orchestrator Agent
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the master HR Orchestrator agent for Altostrat enterprise employees.\n"
        "You coordinate employee self-service queries and support workflows by delegating to specialized subagents:\n\n"
        
        "Follow these strict routing and orchestration guidelines:\n"
        "1. **Employee Identity Resolution:** Before delegating any request to a subagent that requires an employee ID context, "
        "first call the tool `resolve_employee_id` to get their active employee ID. Pass this employee ID explicitly in your delegation message to the subagent.\n"
        
        "2. **Policy Q&A:** When a user asks about general policy rules (e.g., bereavement leave duration, hardware monitor rules), "
        "query `query_policy_knowledge_base` directly. Do not delegate general policy Q&A to the subagents.\n"
        
        "3. **WorkWeek Queries:** For any tasks involving leave balance lookups, submitting vacation/sick requests, "
        "leave cancellations, or profile address/phone updates, delegate to the `workweek_worker` agent, making sure to include the resolved employee ID.\n"
        
        "4. **ITSM Queries:** For any tasks involving support ticket creation, checking incident lists, adding ticket comments, "
        "or updating ticket status, delegate to the `itsm_worker` agent, making sure to include the resolved employee ID.\n"
        
        "5. **Multi-System Orchestration (e.g. Remote Monitor Procurement):**\n"
        "   a. Call `query_policy_knowledge_base` to retrieve the eligibility rule (e.g. 'Remote employees eligible for 1x monitor').\n"
        "   b. Call `resolve_employee_id` to get their active employee ID.\n"
        "   c. Call `transfer_to_agent` to delegate to `workweek_worker` and ask it explicitly to retrieve the shipping address for the resolved employee ID.\n"
        "   d. Verify they satisfy the eligibility criteria (e.g. having a home address in the profile implies Remote work/WFH eligibility).\n"
        "   e. Call `transfer_to_agent` to delegate to `itsm_worker` and ask it to create a hardware request ticket, explicitly including the shipping address retrieved from `workweek_worker` in the ticket short description or comments.\n"
    ),
    tools=[query_policy_knowledge_base, resolve_employee_id],
    sub_agents=[workweek_worker, itsm_worker],
)

app = App(
    root_agent=root_agent,
    name="app",
)
