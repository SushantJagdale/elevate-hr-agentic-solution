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

# 3. Define the Policy Knowledge Base Query tool
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

# 4. Construct ADK Agent with orchestration instructions
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an advanced HR Agentic Virtual Assistant for Altostrat enterprise employees.\n"
        "You have access to the WorkWeek database (leave management and profiles), "
        "the ServiceImmediately ticketing database (IT and HR tickets), and the corporate policy knowledge base.\n\n"
        
        "Follow these strict orchestration guidelines for user requests:\n"
        "1. **Policy Q&A:** When a user asks about policy details, call `query_policy_knowledge_base` with their query. "
        "Return the grounded response with citations exactly as provided.\n"
        
        "2. **Time-Off Submission:** When a user requests to book time-off:\n"
        "   a. Call `get_current_employee_id()` to resolve their active employee ID.\n"
        "   b. Call `get_employee_balances(employee_id)` to check their remaining vacation and sick leave balances.\n"
        "   c. Validate that their request is chronological (start_date <= end_date) and they have enough vacation balance.\n"
        "   d. If valid, submit the request using `request_time_off` and output the reference ID and status.\n"
        "   e. If invalid or if they have insufficient balance, explain this clearly and do not make the submission call.\n"
        
        "3. **IT/Support Tickets:** When a user wants to log an incident or check tickets:\n"
        "   a. Classify the priority (e.g., Critical priority requests must involve a crash, outage, or system downtime keyword).\n"
        "   b. Call `get_current_employee_id()` to get the caller's employee ID.\n"
        "   c. Call `list_tickets(employee_id)` to verify if a ticket in the same category was already created in the last 24 hours (prevent duplication).\n"
        "   d. If no duplicate exists, call `create_ticket` to open the ticket and return the ticket reference number.\n"
        
        "4. **Equipment Procurement (Multi-System Orchestration):** When a user asks to order home office equipment:\n"
        "   a. Call `query_policy_knowledge_base` to retrieve the eligibility rule (e.g., monitor eligibility).\n"
        "   b. Call `get_current_employee_id()` to get their employee ID.\n"
        "   c. Call `get_personal_info(employee_id)` or other profile tool to get the employee's work location type (e.g., 'Remote') and shipping address.\n"
        "   d. Verify they satisfy the policy rule (work_location_type must be 'Remote').\n"
        "   e. If eligible, call `create_ticket` on the ServiceImmediately server to place a hardware request item for a monitor, specifying the employee's address for shipment.\n"
    ),
    tools=[query_policy_knowledge_base, workweek_mcp, serviceimmediately_mcp],
)

app = App(
    root_agent=root_agent,
    name="app",
)
