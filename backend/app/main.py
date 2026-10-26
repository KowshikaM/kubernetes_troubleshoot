"""FastAPI application entrypoint."""

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
import json

settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Kubernetes Troubleshooting Agent backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Ensure the progress and history routers are included (defensive – some reloads missed them earlier)
from app.api.history import router as history_router
from app.api.progress_stream import router as progress_router
app.include_router(history_router)
app.include_router(progress_router)


from fastapi.responses import StreamingResponse
from app.services.insforge_client import get_insforge_client
from app.services.progress import get_queue
from app.kubernetes.kubectl import KubectlExecutor


@app.get("/")
def root() -> dict:
    """Basic service information."""
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
    }


# Lightweight endpoints defined directly to ensure availability across reloads
@app.get('/investigations/history')
def get_history(authorization: str = Header(None)):
    if not authorization:
        return {"status": "error", "error": "Missing authorization header", "data": []}
    user_id = authorization.split(":", 1)[1] if ":" in authorization else "user_placeholder"
    try:
        insforge = get_insforge_client()
        history = insforge.get_investigation_history(user_id)
        return {"status": "success", "data": [h.model_dump() for h in history]}
    except Exception as e:
        return {"status": "error", "error": f"Failed to fetch history: {str(e)}", "data": []}


async def _sse_generator(inv_id: str):
    q = get_queue(inv_id)
    while True:
        msg = await q.get()
        yield f"data: {json.dumps(msg)}\n\n"
        if msg.get("type") in ("done", "error"):
            break


@app.get('/progress/stream/{inv_id}')
async def stream_progress(inv_id: str):
    return StreamingResponse(_sse_generator(inv_id), media_type='text/event-stream')


@app.get('/debug/kube')
def debug_kube():
    """Return which kubeconfig path the app is using and probe kubectl cluster-info."""
    settings_path = settings.KUBECONFIG_PATH
    ke = KubectlExecutor(kubectl_bin=settings.KUBECTL_BIN, kubeconfig_path=settings_path, timeout=10)
    res = ke.run('cluster-info', '--request-timeout=5s')
    return {
        'kubeconfig_path': settings_path,
        'kubectl_success': res.success,
        'kubectl_stdout': res.stdout,
        'kubectl_stderr': res.stderr,
    }