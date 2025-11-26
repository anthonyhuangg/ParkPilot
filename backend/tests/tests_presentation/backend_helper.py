import json

import aiohttp


def print_json_response(res):
    """Pretty-print an HTTP response as JSON if possible."""
    print(f"[HTTP {res.status_code}] {res.text}")
    try:
        print(json.dumps(res.json(), indent=4))
    except Exception:
        pass


async def listen_to_sse(base_sse_url: str, expected_messages: int):
    """
    Connects to an SSE endpoint and listens for N messages.
    Returns a list of received JSON objects.
    """
    updates = []
    async with aiohttp.ClientSession() as session:
        async with session.get(base_sse_url, timeout=None) as resp:
            async for line in resp.content:
                decoded = line.decode().strip()
                if decoded.startswith("data: "):
                    data = json.loads(decoded[6:])
                    print("[SSE] Received:", data)
                    updates.append(data)
                    if len(updates) >= expected_messages:
                        break
    return updates
