"""Root Cause Analyzer.

Consumes the investigation payload, sends it to the LLM as a structured prompt,
and maps the model output into a validated Diagnosis. If the LLM is unavailable
it degrades gracefully instead of crashing the request.
"""

from loguru import logger

from app.ai.confidence import compute_confidence
from app.ai.llm import LLMClient, LLMError
from app.ai.prompts import build_messages
from app.ai.recommender import refine_fix
from app.models.schemas import Diagnosis


def _clean(value, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _as_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_commands(value) -> list[str]:
    if not isinstance(value, list):
        value = [value] if value else []
    return [str(cmd).strip() for cmd in value if str(cmd).strip()]


def _build_diagnosis(raw: dict, evidence: dict) -> Diagnosis:
    """Map the raw model JSON into a validated, confidence-scored Diagnosis."""
    model_confidence = _as_int(raw.get("confidence"))
    score, reasons = compute_confidence(evidence, model_confidence)

    diagnosis = Diagnosis(
        root_cause=_clean(raw.get("root_cause"), "No root cause identified."),
        explanation=_clean(raw.get("explanation")),
        fix=_clean(raw.get("fix")),
        kubectl_commands=_normalize_commands(raw.get("kubectl_commands")),
        prevention=_clean(raw.get("prevention")),
        confidence=score,
        confidence_reasoning=reasons,
    )

    # Guarantee actionable commands even if the model returned none.
    refined = refine_fix(diagnosis.model_dump(), evidence)
    return Diagnosis(**refined)


async def analyze_evidence(evidence: dict) -> dict:
    """Analyze collected evidence and return a diagnosis payload.

    Returns:
        {"ok": True, "diagnosis": Diagnosis} on success, or
        {"ok": False, "reason": str} when the LLM is unavailable.
    """
    client = LLMClient()
    if not client.is_configured():
        logger.error("OPENROUTER_API_KEY not configured; AI diagnosis unavailable")
        return {"ok": False, "reason": "OPENROUTER_API_KEY is not set. Run `insforge ai setup`."}

    try:
        messages = build_messages(evidence)
        raw = await client.chat_json(messages)
    except LLMError as exc:
        logger.exception("AI diagnosis failed: {}", exc)
        return {"ok": False, "reason": str(exc)}

    return {"ok": True, "diagnosis": _build_diagnosis(raw, evidence)}
