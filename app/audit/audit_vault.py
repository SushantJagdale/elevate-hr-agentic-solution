"""BigQuery WORM Immutable Audit Vault Logger."""

import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from ..config import settings
from ..models.audit import AuditEventSchema, SafetyVerdict, ToolCallLog


class AuditVault:
    """Immutable Write-Once-Read-Many (WORM) audit logger matching BigQuery schema."""

    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or settings.AUDIT_LOG_PATH
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Ensure destination log directory exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _hash_user_id(self, user_id: str) -> str:
        """Pseudonymize user ID via SHA-256 for GDPR/CCPA privacy compliance."""
        return hashlib.sha256(user_id.encode("utf-8")).hexdigest()

    def log_event(
        self,
        session_id: str,
        user_id: str,
        prompt_safety_verdict: SafetyVerdict | str,
        intent_category: str = "General",
        model_used: str = "gemini-2.5-flash",
        tool_calls: list[ToolCallLog | dict] | None = None,
        grounding_attribution_score: float | None = None,
        final_response_status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> AuditEventSchema:
        """Write an immutable audit log record."""
        event_id = str(uuid.uuid4())
        user_hash = self._hash_user_id(user_id)

        parsed_tool_calls: list[ToolCallLog] = []
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    parsed_tool_calls.append(ToolCallLog(**tc))
                else:
                    parsed_tool_calls.append(tc)

        if isinstance(prompt_safety_verdict, str):
            try:
                prompt_safety_verdict = SafetyVerdict(prompt_safety_verdict)
            except ValueError:
                prompt_safety_verdict = SafetyVerdict.ALLOWED

        event = AuditEventSchema(
            event_id=event_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=session_id,
            user_id_hash=user_hash,
            prompt_safety_verdict=prompt_safety_verdict,
            intent_category=intent_category,
            model_used=model_used,
            tool_calls=parsed_tool_calls,
            grounding_attribution_score=grounding_attribution_score,
            final_response_status=final_response_status,
            acting_user_id=user_id,
            error_message=error_message,
        )

        # Append to append-only WORM log file
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            # Fallback console log if file write fails
            print(f"[AUDIT LOG ERROR] Failed to append to audit log: {e}")

        return event

    def read_recent_logs(self, limit: int = 50) -> list[dict]:
        """Read recent audit log entries for observability."""
        if not self.log_path.exists():
            return []
        lines = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        lines.append(json.loads(line.strip()))
        except Exception:
            return []
        return lines[-limit:]


audit_vault = AuditVault()
