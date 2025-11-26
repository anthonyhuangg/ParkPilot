import asyncio
import json


class SSEManager:
    """Manages Server-Sent Events (SSE) connections and broadcasts messages to
    subscribers."""

    def __init__(self):
        self.subscribers = set()

    async def subscribe(self):
        """
        Generator that yields SSE-formatted messages for a single client.

        Yields:
            str: Properly formatted SSE message chunks (text/event-stream).

        Raises:
            asyncio.CancelledError: When the client disconnects,
                                    triggers cleanup.
        """
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            self.subscribers.remove(queue)
            raise

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all subscribed clients.

        Args:
            message (dict): The message to broadcast to all subscribers.
        """
        for queue in list(self.subscribers):
            try:
                await queue.put(message)
            except Exception:
                self.subscribers.discard(queue)


sse_manager = SSEManager()
