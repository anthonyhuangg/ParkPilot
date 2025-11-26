from fastapi import APIRouter, Request
from infrastructure.events import get_sse_stream

router = APIRouter()


@router.get("/sse")
async def sse_endpoint(request: Request, lot_id: int | None = None):
    """
    SSE endpoint exposed to clients.
    Optionally filters updates by parking lot ID.

    Args:
        request: The incoming HTTP request.
        lot_id: Optional parking lot ID to filter events.

    Returns:
        An SSE event stream response.
    """
    return get_sse_stream(request=request, lot_id=lot_id)
