import os
import sys
import uuid
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from google.genai import types
from google.adk.runners import InMemoryRunner
from app.agent import root_agent


# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hr_server")

app = FastAPI(title="Enterprise HR Agentic Virtual Assistant API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK Runner for root_agent
runner = InMemoryRunner(agent=root_agent)

# Store session memory map (session_id -> adk_session)
active_sessions: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@app.get("/")
async def serve_index():
    """Serve main frontend UI HTML."""
    static_index = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return HTMLResponse("<h2>Enterprise HR Virtual Assistant Server Running</h2>")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat API endpoint running root_agent and capturing detailed execution trace telemetry."""
    user_prompt = request.message.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Create or retrieve ADK session
        if session_id not in active_sessions:
            adk_session = await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id="default_user"
            )
            active_sessions[session_id] = adk_session.id

        real_session_id = active_sessions[session_id]

        # Prepare Content Input
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        )

        response_texts: List[str] = []
        traces: List[Dict[str, Any]] = []
        visited_agents: List[str] = []

        # Execute async run and stream events
        async for event in runner.run_async(
            user_id="default_user",
            session_id=real_session_id,
            new_message=user_content
        ):
            author = getattr(event, "author", "app")
            if author and author not in visited_agents:
                visited_agents.append(author)
                traces.append({
                    "type": "transfer",
                    "agent": author,
                    "detail": f"Agent Context Transferred to [{author}]"
                })

            if hasattr(event, "content") and event.content:
                parts = event.content.parts or []
                for part in parts:
                    # Capture Text Responses
                    if part.text:
                        response_texts.append(part.text)

                    # Capture Tool Calls
                    if part.function_call:
                        func_name = part.function_call.name
                        func_args = dict(part.function_call.args or {})
                        traces.append({
                            "type": "tool_call",
                            "agent": author,
                            "tool_name": func_name,
                            "args": func_args,
                            "detail": f"Executing tool `{func_name}`"
                        })

                    # Capture Tool Responses
                    if part.function_response:
                        func_name = part.function_response.name
                        response_payload = part.function_response.response
                        traces.append({
                            "type": "tool_response",
                            "agent": author,
                            "tool_name": func_name,
                            "result": response_payload,
                            "detail": f"Tool `{func_name}` completed"
                        })

        final_response = "\n".join(response_texts).strip() or "No text output produced."
        primary_agent = visited_agents[-1] if visited_agents else "app"

        return {
            "status": "success",
            "session_id": session_id,
            "agent": primary_agent,
            "visited_agents": visited_agents,
            "response": final_response,
            "traces": traces
        }

    except Exception as e:
        logger.exception("Error executing agent turn")
        return {
            "status": "error",
            "session_id": session_id,
            "message": str(e),
            "response": f"⚠️ An error occurred while processing your request: {str(e)}"
        }

# Mount static assets directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
