import asyncio
from typing import Dict

# A simple in-memory progress pub/sub for investigation events.
# Keyed by investigation id -> asyncio.Queue

_queues: Dict[str, asyncio.Queue] = {}


def get_queue(inv_id: str) -> asyncio.Queue:
    if inv_id not in _queues:
        _queues[inv_id] = asyncio.Queue()
    return _queues[inv_id]


async def publish(inv_id: str, message: dict) -> None:
    q = get_queue(inv_id)
    await q.put(message)


async def subscribe(inv_id: str):
    """Async generator that yields messages for the given investigation id."""
    q = get_queue(inv_id)
    while True:
        message = await q.get()
        yield message
        # stop iteration if a terminal event is published
        if message.get("type") in ("done", "error"):
            break
