"""Pydantic request/response schemas."""

from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Payload returned by the GET /health endpoint."""

    status: str
    service: str


class Diagnosis(BaseModel):
    """AI diagnosis produced by the root cause analyzer."""

    root_cause: str = ""
    explanation: str = ""
    fix: str = ""
    kubectl_commands: list[str] = []
    prevention: str = ""
    confidence: int = 0
    confidence_reasoning: list[str] = []


class InvestigateRequest(BaseModel):
    """Optional parameters for a Kubernetes investigation."""

    namespace: str | None = None
    # Optional kubeconfig context name to use for this investigation (optional)
    context: str | None = None


class InvestigateResponse(BaseModel):
    """Payload returned by POST /investigate (evidence + AI diagnosis)."""

    status: str
    error: str | None = None
    investigation: dict = {}
    diagnosis: Diagnosis | None = None


class InvestigationHistoryEntry(BaseModel):
    """A saved investigation from history."""

    id: str
    user_id: str
    namespace: str | None = None
    root_cause: str
    explanation: str
    confidence: int
    status: str  # "success", "partial", "failed"
    created_at: datetime
    diagnosis_data: dict = {}


class InvestigationHistoryResponse(BaseModel):
    """Payload returned by GET /investigations/history."""

    status: str
    data: list[InvestigationHistoryEntry] = []
    error: str | None = None
