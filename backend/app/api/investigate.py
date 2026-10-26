"""POST /investigate endpoint: collect Kubernetes evidence + AI diagnosis."""

import asyncio

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from app.ai.analyzer import analyze_evidence
from app.kubernetes.investigation import InvestigationService
from app.models.schemas import InvestigateRequest, InvestigateResponse
from app.services.insforge_client import get_insforge_client
from app.services.progress import get_queue

router = APIRouter(tags=["investigate"])



@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(
    request: InvestigateRequest | None = None,
    authorization: str = Header(None),
) -> InvestigateResponse:
    """Investigate the cluster, then reason about the evidence with the AI agent."""
    namespace = request.namespace if request else None
    # Extract optional context from the request (we extended InvestigateRequest later)
    context = getattr(request, 'context', None) if request else None

    # Extract user id from authorization header if available (format: user:<id>)
    user_channel = None
    if authorization and ":" in authorization:
        user_channel = authorization.split(":", 1)[1]

    # Create a fresh InvestigationService so it reads current settings (avoids stale cached instance)
    investigation_service = InvestigationService(context=context)

    # Run the investigation in a thread so the main event loop isn't blocked
    result = await asyncio.to_thread(investigation_service.investigate, namespace, user_channel)

    if result["status"] != "success":
        return InvestigateResponse(
            status=result["status"],
            error=result.get("error"),
            investigation=result.get("investigation", {}),
        )

    evidence = result["investigation"]

    # Publish progress updates during analysis (this is simple — real-time step-by-step
    # publishing would be inserted inside InvestigationService in a more advanced flow).
    insforge = get_insforge_client()
    try:
        insforge.publish_progress('global', {"type": "info", "message": "AI reasoning started"})
    except Exception:
        pass

    analysis = await analyze_evidence(evidence)
    if not analysis["ok"]:
        try:
            insforge.publish_progress('global', {"type": "error", "message": "AI analysis failed"})
        except Exception:
            pass
        return InvestigateResponse(
            status="partial",
            error=f"AI analysis unavailable: {analysis['reason']}",
            investigation=evidence,
        )

    response = InvestigateResponse(
        status="success",
        investigation=evidence,
        diagnosis=analysis["diagnosis"],
    )

    # Save investigation to history if user is authenticated
    if authorization and response.diagnosis:
        try:
            # NOTE: For now the frontend sends a placeholder token of the form "user:<user_id>".
            # Extract user_id from that token. In production validate JWT properly.
            user_id = authorization.split(":", 1)[1] if ":" in authorization else "user_placeholder"

            insforge = get_insforge_client()
            insforge.save_investigation(
                user_id=user_id,
                namespace=namespace,
                root_cause=response.diagnosis.root_cause,
                explanation=response.diagnosis.explanation,
                confidence=response.diagnosis.confidence,
                status=response.status,
                diagnosis_data=response.diagnosis.model_dump(),
            )

            # Publish progress final event to the investigation channel
            try:
                insforge.publish_progress(user_id, {"type": "done", "diagnosis": response.diagnosis.model_dump()})
            except Exception:
                pass
        except Exception:
            # Log but don't fail the investigation if history save fails
            pass

    return response


@router.get("/investigations/history")
async def get_history(
    authorization: str = Header(None),
):
    """Fetch investigation history for the authenticated user.

    This endpoint mirrors the original /investigations/history implementation.
    """
    if not authorization:
        return {"status": "error", "error": "Missing authorization header", "data": []}

    user_id = authorization.split(":", 1)[1] if ":" in authorization else "user_placeholder"
    try:
        insforge = get_insforge_client()
        history = insforge.get_investigation_history(user_id)
        # Convert Pydantic models to dicts
        return {"status": "success", "data": [h.model_dump() for h in history]}
    except Exception as e:
        return {"status": "error", "error": f"Failed to fetch history: {str(e)}", "data": []}


async def _sse_generator(inv_id: str):
    q = get_queue(inv_id)
    while True:
        msg = await q.get()
        yield f"data: {msg}\n\n"
        if msg.get("type") in ("done", "error"):
            break


@router.get("/progress/stream/{inv_id}")
async def stream_progress(request: Request, inv_id: str):
    return StreamingResponse(_sse_generator(inv_id), media_type="text/event-stream")
