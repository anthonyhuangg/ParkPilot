import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from infrastructure.scheduler import schedule_ttl_reset, _reset_task
from database.models.parking import NodeStatus


@pytest.mark.asyncio
async def test_schedule_ttl_reset_creates_task():
    with patch("infrastructure.scheduler.asyncio.create_task") as mock_task:
        schedule_ttl_reset(1, 10, 5)
        mock_task.assert_called_once()
        args, kwargs = mock_task.call_args
        assert "_reset_task" in str(args[0])


# Success: Node expired -> reset, graph updated, broadcast called
@pytest.mark.asyncio
async def test_reset_task_resets_node_and_broadcasts():
    # Mock DB + repo + node
    mock_db = MagicMock()
    mock_repo = MagicMock()
    mock_node = MagicMock()

    mock_node.status = NodeStatus.RESERVED
    mock_node.expires_at = datetime.utcnow() - timedelta(seconds=1)  # expired

    mock_repo.get_node.return_value = mock_node

    mock_graph = MagicMock()
    mock_graph.nodes = {10: {"status": None}}

    mock_parking_service = MagicMock()
    mock_parking_service.graphs = {1: mock_graph}

    with patch("infrastructure.scheduler.SessionLocal", return_value=mock_db):
        with patch(
            "infrastructure.scheduler.ParkingRepository", return_value=mock_repo
        ):
            with patch(
                "application.services.parking_service.parking_service",
                mock_parking_service,
            ):
                with patch(
                    "infrastructure.scheduler.broadcast_event",
                    new=AsyncMock(),
                ) as mock_broadcast:
                    await _reset_task(1, 10, ttl=0)

                    assert mock_node.status == NodeStatus.AVAILABLE
                    assert mock_node.expires_at is None

                    mock_repo.save.assert_called_once_with(mock_node)

                    assert mock_graph.nodes[10]["status"] == NodeStatus.AVAILABLE.value

                    mock_broadcast.assert_awaited_once()
                    mock_db.close.assert_called_once()


# Failure: Node not expired -> no reset
@pytest.mark.asyncio
async def test_reset_task_no_reset_when_not_expired():
    mock_db = MagicMock()
    mock_repo = MagicMock()
    mock_node = MagicMock()

    mock_node.status = NodeStatus.RESERVED
    mock_node.expires_at = datetime.utcnow() + timedelta(seconds=100)

    mock_repo.get_node.return_value = mock_node

    mock_graph = MagicMock()
    mock_graph.nodes = {10: {}}

    mock_parking_service = MagicMock()
    mock_parking_service.graphs = {1: mock_graph}

    with patch("infrastructure.scheduler.SessionLocal", return_value=mock_db):
        with patch(
            "infrastructure.scheduler.ParkingRepository", return_value=mock_repo
        ):
            with patch(
                "application.services.parking_service.parking_service",
                mock_parking_service,
            ):
                with patch(
                    "infrastructure.scheduler.broadcast_event",
                    new=AsyncMock(),
                ) as mock_broadcast:
                    await _reset_task(1, 10, ttl=0)

                    # Should NOT save or broadcast
                    mock_repo.save.assert_not_called()
                    mock_broadcast.assert_not_awaited()

                    mock_db.close.assert_called_once()


# Failure: Node does not exist
@pytest.mark.asyncio
async def test_reset_task_no_node_found():
    mock_db = MagicMock()
    mock_repo = MagicMock()

    mock_repo.get_node.return_value = None  # simulate no node found

    with patch("infrastructure.scheduler.SessionLocal", return_value=mock_db):
        with patch(
            "infrastructure.scheduler.ParkingRepository", return_value=mock_repo
        ):
            with patch(
                "infrastructure.scheduler.broadcast_event",
                new=AsyncMock(),
            ) as mock_broadcast:
                await _reset_task(1, 10, ttl=0)

                mock_repo.save.assert_not_called()
                mock_broadcast.assert_not_awaited()

                mock_db.close.assert_called_once()
