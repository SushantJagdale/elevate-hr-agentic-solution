"""FastAPI Application Server for Enterprise HR Agentic Virtual Assistant."""

import json
import os
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config import settings
from ..models.session import UserContext
from ..services.policy_knowledge_service import policy_service
from ..services.workweek_service import workweek_db
from ..audit.audit_vault import audit_vault
from ..agent.orchestrator import hr_orchestrator

app = FastAPI(
    title="Enterprise HR Agentic Virtual Assistant API",
    description="GCP-native Serverless Agentic Assistant for HR, Leave, ITSM, and Policy Guidance",
    version="2.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    user_id: str | None = "E1209"


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "enterprise-hr-assistant",
        "version": "2.1.0",
        "timestamp": time.time(),
        "policy_chunks_indexed": len(policy_service._chunks),
        "retrieval_mode": settings.RETRIEVAL_MODE,
        "gcp_project": settings.PROJECT_ID,
    }


@app.get("/api/employee/me")
def get_current_user():
    """Return currently authenticated session employee profile."""
    profile = workweek_db.get_profile("E1209")
    if profile:
        return profile.model_dump()
    return {"error": "User not found"}


@app.get("/api/policies")
def list_policies():
    """List available indexed policy documents."""
    return policy_service.list_all_policies()


@app.get("/api/audit/logs")
def get_audit_logs(limit: int = 50):
    """Retrieve immutable audit vault logs."""
    return audit_vault.read_recent_logs(limit=limit)


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Standard REST Chat turn endpoint."""
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    result = hr_orchestrator.run_turn(
        session_id=session_id,
        user_prompt=req.prompt,
    )
    return result


@app.get("/api/chat/stream")
def stream_chat(prompt: str, session_id: str = ""):
    """Server-Sent Events (SSE) streaming chat endpoint."""
    s_id = session_id or f"session_{uuid.uuid4().hex[:8]}"

    def event_generator():
        # Execute turn
        result = hr_orchestrator.run_turn(session_id=s_id, user_prompt=prompt)
        text = result.get("response", "")
        
        # Stream chunks with SSE formatting
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = {
                "chunk": chunk,
                "done": False,
                "session_id": s_id,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(0.015)  # simulate natural streaming

        # Send final metadata event
        final_payload = {
            "done": True,
            "session_id": s_id,
            "tool_calls": result.get("tool_calls", []),
            "citations": result.get("citations", []),
            "grounding_score": result.get("grounding_score"),
            "latency_ms": result.get("latency_ms"),
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount static web assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the Web Chat UI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>Enterprise HR Agentic Virtual Assistant API is running!</h1>"
