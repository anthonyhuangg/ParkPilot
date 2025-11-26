import asyncio
from datetime import datetime
from database import SessionLocal
from database.models.parking import NodeStatus
from infrastructure.events import broadcast_event
from persistence.parking_repository import ParkingRepository


def schedule_ttl_reset(lot_id: int, node_id: int, ttl: int):
    """Schedule background task that automatically resets a RESERVED spot
    to AVAILABLE after ttl seconds"""
    asyncio.create_task(_reset_task(lot_id, node_id, ttl))


async def _reset_task(lot_id: int, node_id: int, ttl: int):
    """
    Background coroutine executed after ttl seconds

    Args:
        lot_id (int): Parking lot ID
        node_id (int): Parking node ID
        ttl (int): delay before checking expiration
    """
    await asyncio.sleep(ttl)
    db = SessionLocal()
    repo = ParkingRepository(db)
    node = repo.get_node(node_id)

    if (
        node
        and node.status == NodeStatus.RESERVED
        and node.expires_at
        and node.expires_at <= datetime.utcnow()
    ):
        node.status = NodeStatus.AVAILABLE
        node.expires_at = None
        repo.save(node)

        from application.services.parking_service import parking_service

        G = parking_service.graphs.get(lot_id)
        if G and node_id in G.nodes:
            G.nodes[node_id]["status"] = NodeStatus.AVAILABLE.value

        await broadcast_event(
            {
                "lot_id": lot_id,
                "node_id": node_id,
                "status": node.status.value,
                "expires_at": None,
            }
        )
    db.close()
