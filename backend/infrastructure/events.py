import asyncio
import json

from fastapi import Request
from fastapi.responses import StreamingResponse

# Each subscriber is a tuple: (queue, lot_id)
_subscribers: set[tuple[asyncio.Queue, int | None]] = set()


async def event_stream(request: Request, lot_id: int | None = None):
    """
    Event generator for SSE clients.

    Args:
        request (Request): request object (used to detect client disconnect)
        lot_id (int | None): If provided, client only receives events for this
                             parking lot
    """
    queue = asyncio.Queue()
    subscriber = (queue, lot_id)
    _subscribers.add(subscriber)

    try:
        while True:
            if await request.is_disconnected():
                break

            try:
                data = await asyncio.wait_for(queue.get(), timeout=15)

                if lot_id is None or data.get("lot_id") == lot_id:
                    yield f"data: {json.dumps(data)}\n\n"

            except asyncio.TimeoutError:
                yield ":\n\n"

    finally:
        _subscribers.discard(subscriber)


async def broadcast_event(data: dict):
    """
    Sends an event to all subscribers that are listening

    Args:
        data (dict): event payload
    """
    for queue, subscribed_lot_id in list(_subscribers):
        try:
            if subscribed_lot_id is None or data.get("lot_id") == subscribed_lot_id:
                await queue.put(data)
        except Exception:
            _subscribers.discard((queue, subscribed_lot_id))


def get_sse_stream(request: Request, lot_id: int | None = None):
    """Returns the SSE stream response for the given lot."""
    return StreamingResponse(
        event_stream(request, lot_id), media_type="text/event-stream"
    )
