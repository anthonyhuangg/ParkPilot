import asyncio
import pytest
from fastapi import Request
from fastapi.responses import StreamingResponse
from infrastructure import events


# broadcast_event – normal delivery
@pytest.mark.asyncio
async def test_broadcast_event_to_subscribers():
    q1, q2 = asyncio.Queue(), asyncio.Queue()
    events._subscribers.clear()
    events._subscribers.update({(q1, 1), (q2, None)})

    data = {"lot_id": 1, "node_id": 5, "status": "AVAILABLE"}
    await events.broadcast_event(data)

    assert await q1.get() == data
    assert await q2.get() == data


# broadcast_event – remove broken subscriber
@pytest.mark.asyncio
async def test_broadcast_event_removes_bad_subscriber():
    q = asyncio.Queue()

    events._subscribers.clear()
    events._subscribers.add((q, 1))

    async def bad_put(_):
        raise RuntimeError("fail")

    q.put = bad_put

    await events.broadcast_event({"lot_id": 1})

    assert (q, 1) not in events._subscribers


# event_stream – covers data yield + disconnect (break)
@pytest.mark.asyncio
async def test_event_stream_data_and_disconnect(monkeypatch):
    queue = asyncio.Queue()

    # Fake request that stays connected once, then disconnects
    class FakeRequest:
        def __init__(self):
            self.calls = 0

        async def is_disconnected(self):
            self.calls += 1
            return self.calls >= 2  # second call = disconnect

    request = FakeRequest()

    events._subscribers.clear()

    async def fake_wait_for(coro, timeout):
        await queue.put({"lot_id": 1, "msg": "hello"})
        return await queue.get()

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    gen = events.event_stream(request, lot_id=1)

    out1 = await gen.__anext__()
    assert out1.startswith("data: ")

    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()

    assert len(events._subscribers) == 0


# event_stream – heartbeat timeout branch
@pytest.mark.asyncio
async def test_event_stream_heartbeat(monkeypatch):
    # Fake request that never disconnects
    class FakeRequest:
        async def is_disconnected(self):
            return False

    request = FakeRequest()
    events._subscribers.clear()

    # Force TimeoutError in asyncio.wait_for
    async def fake_wait_for(coro, timeout):
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    gen = events.event_stream(request, lot_id=1)

    # Should yield heartbeat
    hb = await gen.__anext__()
    assert hb == ":\n\n"

    await gen.aclose()
    events._subscribers.clear()


def test_get_sse_stream_returns_streaming_response():
    request = Request(scope={"type": "http"})
    resp = events.get_sse_stream(request, lot_id=1)
    assert isinstance(resp, StreamingResponse)
    assert resp.media_type == "text/event-stream"
