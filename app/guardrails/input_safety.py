"""Input Safety & Prompt Injection Guardrail (Google Cloud DLP & Vertex AI Safety Filter emulator)."""

import re
from typing import Tuple
from ..models.audit import SafetyVerdict


class InputSafetyGuard:
    """Multi-layered input inspection for prompt injection, SPII redaction, and topic containment."""

    # Prompt injection and jailbreak heuristic patterns
    INJECTION_PATTERNS = [
        r"(?i)(ignore|disregard|forget|bypass)\s+.*(instruction|prompt|rule|guideline)",
        r"(?i)system\s*prompt\s*(override|leak|dump|show)",
        r"(?i)you\s+are\s+now\s+in\s+dan\s+mode",
        r"(?i)bypass\s+all\s+(security|guardrails|safety)",
        r"(?i)jailbreak",
        r"(?i)repeat\s+(the\s+)?(secret|internal|system)\s+(prompt|key|token)",
        r"(?i)print\s+.*(instruction|system\s*prompt|api\s*key|secret)",
        r"(?i)dump\s+.*(secret|key|prompt|instruction)",
    ]

    # Sensitive PII regex patterns (Cloud DLP InfoTypes emulator)
    SPII_PATTERNS = {
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "SSN_US": r"\b\d{3}-\d{2}-\d{4}\b",
        "SINGAPORE_NRIC_FIN": r"\b[STFGQM]\d{7}[A-Z]\b",
        "PASSWORD_SECRET": r"(?i)(password|secret_key|api_token)\s*[:=]\s*['\"]?(\w+)['\"]?",
    }

    # Off-topic containment keywords (unrelated to workplace/HR/IT)
    OFF_TOPIC_PATTERNS = [
        r"(?i)\b(write\s+a\s+poem\s+about\s+crypto|bitcoin\s+price|how\s+to\s+make\s+a\s+bomb|illegal\s+drugs)\b"
    ]

    def check_injection(self, text: str) -> Tuple[bool, str]:
        """Detect prompt injection or jailbreak attempts."""
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True, f"Prompt injection detected by rule: {pattern}"
        return False, ""

    def mask_spii(self, text: str) -> Tuple[str, list[str]]:
        """Redact sensitive PII elements in user prompt."""
        masked_text = text
        redacted_types = []

        for pii_type, pattern in self.SPII_PATTERNS.items():
            if pii_type == "PASSWORD_SECRET":
                def replace_pwd(match):
                    redacted_types.append("PASSWORD")
                    return f"{match.group(1)}: [REDACTED_SECRET]"
                masked_text = re.sub(pattern, replace_pwd, masked_text)
            else:
                matches = re.findall(pattern, masked_text)
                if matches:
                    redacted_types.append(pii_type)
                    masked_text = re.sub(pattern, f"[REDACTED_{pii_type}]", masked_text)

        return masked_text, redacted_types

    def check_topic_containment(self, text: str) -> Tuple[bool, str]:
        """Verify prompt is within HR, workplace, IT, equipment, or policy domain."""
        for pattern in self.OFF_TOPIC_PATTERNS:
            if re.search(pattern, text):
                return False, "Prompt is outside HR / Workplace support domain."
        return True, ""

    def evaluate_input(self, text: str) -> Tuple[SafetyVerdict, str, str]:
        """Run complete input safety scan. Returns (Verdict, SanitizedText, Reason)."""
        # 1. Check for prompt injection
        is_inj, reason = self.check_injection(text)
        if is_inj:
            return SafetyVerdict.BLOCKED_INJECTION, text, reason

        # 2. Check topic containment
        in_topic, topic_reason = self.check_topic_containment(text)
        if not in_topic:
            return SafetyVerdict.BLOCKED_DOMAIN, text, topic_reason

        # 3. Mask Sensitive PII
        sanitized_text, masked_types = self.mask_spii(text)

        return SafetyVerdict.ALLOWED, sanitized_text, "Input passed all security guardrails."


input_safety_guard = InputSafetyGuard()
