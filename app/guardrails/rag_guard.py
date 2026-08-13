"""RAG Grounding Guardrail (Attribution & Hallucination Filter)."""

from typing import Tuple
from ..config import settings
from ..models.rag import GroundingResult


class RAGGroundingGuardrail:
    """Evaluates grounding attribution scores and enforces deterministic policy refusal."""

    REFUSAL_MESSAGE = (
        "I am sorry, but official policy records do not contain sufficient information "
        "regarding this request. Please contact HR at hr-support@corp.internal or your manager for further assistance."
    )

    def evaluate_grounding(
        self, grounding_result: GroundingResult, threshold: float | None = None
    ) -> Tuple[bool, str]:
        """Verify attribution score against threshold."""
        min_threshold = threshold or settings.GROUNDING_ATTRIBUTION_THRESHOLD

        if not grounding_result.chunks or grounding_result.attribution_score < min_threshold:
            return False, self.REFUSAL_MESSAGE

        return True, "Policy grounding verified."


rag_guard = RAGGroundingGuardrail()
