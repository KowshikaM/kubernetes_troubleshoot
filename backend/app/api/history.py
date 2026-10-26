"""Investigation history endpoints."""

from fastapi import APIRouter, Header

from app.models.schemas import InvestigationHistoryResponse
from app.services.insforge_client import get_insforge_client

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("/history", response_model=InvestigationHistoryResponse)
async def get_investigation_history(
    authorization: str = Header(None),
) -> InvestigationHistoryResponse:
    """Fetch investigation history for the authenticated user.

    Requires a valid InsForge authentication token.
    """
    if not authorization:
        return InvestigationHistoryResponse(
            status="error",
            error="Missing authorization header",
            data=[],
        )

    # Extract user_id from JWT (in production, this would be verified by InsForge middleware)
    # For now, we'll use a placeholder
    user_id = "user_placeholder"

    try:
        insforge = get_insforge_client()
        history = insforge.get_investigation_history(user_id)
        
        return InvestigationHistoryResponse(
            status="success",
            data=history,
        )
    except Exception as e:
        return InvestigationHistoryResponse(
            status="error",
            error=f"Failed to fetch history: {str(e)}",
            data=[],
        )
