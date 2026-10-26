"""AI reasoning layer.

The AI Kubernetes Agent: turns collected cluster evidence into a structured
diagnosis (root cause, fix, kubectl commands, prevention, confidence) using
OpenRouter via the InsForge-provided API key.
"""

from loguru import logger

from app.ai.analyzer import analyze_evidence


async def analyze_cluster(cluster_data: dict) -> dict:
    """Analyze collected cluster evidence and return the diagnosis.

    Returns:
        {"status": "done", "diagnosis": Diagnosis} on success, or
        {"status": "pending", "reason": str} when the LLM is unavailable.
    """
    logger.info("analyze_cluster: analyzing Kubernetes evidence")
    result = await analyze_evidence(cluster_data)
    if not result["ok"]:
        return {"status": "pending", "reason": result["reason"], "diagnosis": None}
    return {"status": "done", "diagnosis": result["diagnosis"]}
