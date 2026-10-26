"""Server-sent events (SSE) endpoint for streaming investigation progress.

This lightweight implementation uses the local in-memory progress queue (app.services.progress)
for development. When InsForge realtime is integrated, this endpoint can be adapted to use
InsForge realtime channels or WebSockets.
"""

import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.services.progress import subscribe, get_queue

router = APIRouter(prefix="/progress", tags=["progress"]) 


async def event_stream(inv_id: str):
    # Async generator yielding SSE-formatted messages
    q = get_queue(inv_id)
    while True:
        message = await q.get()
        # Convert message dict to JSON string
        yield f"data: {message}\n\n"
        if message.get("type") in ("done", "error"):
            break


@router.get("/stream/{inv_id}")
async def stream_progress(request: Request, inv_id: str):
    generator = event_stream(inv_id)
    return StreamingResponse(generator, media_type="text/event-stream")
