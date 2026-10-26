"""Application services and orchestration."""

from loguru import logger

from app.ai.agent import analyze_cluster
from app.kubernetes.investigation import InvestigationService

_investigation_service = InvestigationService()


async def run_diagnosis(namespace: str | None = None) -> dict:
    """Run the on-demand diagnosis pipeline (AI step is still a placeholder).

    Future flow:
        1. Collect Kubernetes evidence.
        2. Ask the AI agent for a root cause + suggested fix.
        3. Return the diagnosis.
    """
    logger.info("run_diagnosis called namespace={}", namespace)

    result = _investigation_service.investigate(namespace=namespace)

    return {
        "status": result["status"],
        "investigation": result.get("investigation", {}),
        "diagnosis": await analyze_cluster(result.get("investigation", {})),
    }
