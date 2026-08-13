"""Output Safety & Redaction Interceptor."""

import re
from typing import Tuple


class OutputSafetyGuard:
    """Scans and sanitizes outgoing responses for sensitive leakage or ungrounded formatting."""

    SECRET_LEAK_PATTERNS = [
        r"mock_[a-zA-Z0-9_]+_sec_mgr_[a-zA-Z0-9_]+",
        r"AIza[0-9A-Za-z_-]{35}",
        r"Bearer\s+[a-zA-Z0-9_\-\.]+",
    ]

    def sanitize_output(self, response_text: str) -> Tuple[str, bool]:
        """Redact any accidental internal secrets or bearer tokens."""
        sanitized = response_text
        had_leak = False

        for pattern in self.SECRET_LEAK_PATTERNS:
            if re.search(pattern, sanitized):
                had_leak = True
                sanitized = re.sub(pattern, "[REDACTED_SECRET]", sanitized)

        return sanitized, had_leak


output_safety_guard = OutputSafetyGuard()
