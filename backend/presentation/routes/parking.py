from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from application.models.parking import (
    RouteResponse,
    LotResponse,
    LotSummary,
    MultiLotSummary,
    SpotRecommendation,
    ExitRouteResponse,
    AlternativeRoutesResponse,
    PathValidationRequest,
    PathValidationResponse,
    EdgeResponse,
)
from typing import List
from datetime import datetime
from persistence.occupancy_repository import OccupancyRepository
from application.services.parking_service import parking_service
from database import get_db

router = APIRouter(prefix="/parking", tags=["parking"])


@router.get("/{lot_id}/nodes", response_model=LotResponse)
def list_nodes(lot_id: int, db: Session = Depends(get_db)):
    """
    List nodes in a parking lot.

    Args:
        lot_id: The ID of the parking lot.
        db: Database session.

    Returns:
        LotResponse: Details of the parking lot nodes.

    Raises:
        HTTPException: If the graph for the lot is not loaded.
    """
    G = parking_service.graphs.get(lot_id)
    if not G:
        raise HTTPException(status_code=404, detail="Graph not loaded")

    nodes = []
    for nid, data in G.nodes(data=True):
        node = {
            "id": nid,
            "type": data.get("type"),
            "x": data.get("x", 0.0),
            "y": data.get("y", 0.0),
            "status": data.get("status"),
        }
        if data.get("orientation") is not None:
            node["orientation"] = data["orientation"]
        if data.get("label") is not None:
            node["label"] = data["label"]
        nodes.append(node)

    if nodes:
        max_x = max(node["x"] for node in nodes)
        max_y = max(node["y"] for node in nodes)
        min_x = min(node["x"] for node in nodes)
        min_y = min(node["y"] for node in nodes)
        rows = int(max_y - min_y) + 1
        cols = int(max_x - min_x) + 1
    else:
        rows = cols = 0

    return {
        "lot_id": lot_id,
        "dimensions": {"rows": rows, "cols": cols},
        "nodes": nodes,
    }


@router.get("/{lot_id}/road-edges", response_model=List[EdgeResponse])
def list_road_edges(lot_id: int, db: Session = Depends(get_db)):
    """
    List road edges in a parking lot.

    Args:
        lot_id: The ID of the parking lot.
        db: Database session.

    Returns:
        List[EdgeResponse]: Details of the road edges.

    Raises:
        HTTPException: If an error occurs while retrieving road edges.
    """
    try:
        return parking_service.get_road_edges(lot_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lot_id}/route", response_model=RouteResponse)
def get_route(lot_id: int, start: int, end: int):
    """
    Get the shortest route between two nodes in a parking lot.

    Args:
        lot_id: The ID of the parking lot.
        start: The starting node ID.
        end: The ending node ID.

    Returns:
        RouteResponse: The shortest route details.

    Raises:
        HTTPException: If route calculation fails.
    """
    try:
        return parking_service.shortest_path(lot_id, start, end)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/multilot/summary", response_model=MultiLotSummary)
def get_lot_summaries(db: Session = Depends(get_db)):
    """
    Get summaries for multiple parking lots.

    Args:
        db: Database session.

    Returns:
        MultiLotSummary: Summaries of multiple parking lots.

    Raises:
        HTTPException: If an error occurs while retrieving summaries.
    """
    try:
        return parking_service.get_lot_summaries(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lot_id}/update_status")
async def update_node_status(
    lot_id: int, node_id: int, status: str, ttl: int, db: Session = Depends(get_db)
):
    """
    Update the status of a parking node.

    Args:
        lot_id: The ID of the parking lot.
        node_id: The ID of the parking node.
        status: The new status of the node.
        ttl: Time-to-live for the status update.
        db: Database session.

    Returns:
        The result of the status update operation.

    Raises:
        HTTPException: If the update fails.
    """
    try:
        result = await parking_service.update_node_status(
            lot_id, node_id, status, ttl, db
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lot_id}/find-spot", response_model=SpotRecommendation)
def find_available_spot(
    lot_id: int,
    entrance_id: int,
    orientation: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """
    Find the nearest available parking spot from an entrance.

    Args:
        lot_id: The ID of the parking lot.
        entrance_id: The ID of the entrance node.
        orientation: Optional preferred orientation for the parking spot.
        db: Database session.

    Returns:
        SpotRecommendation: The recommended parking spot details.

    Raises:
        HTTPException: If no available spots are found.
    """
    preferences = {}
    if orientation is not None:
        preferences["orientation"] = orientation

    result = parking_service.find_nearest_available_spot(
        lot_id, entrance_id, preferences
    )

    if not result:
        raise HTTPException(status_code=404, detail="No available spots found")

    return result


@router.get("/{lot_id}/route-to-exit", response_model=ExitRouteResponse)
def get_exit_route(lot_id: int, current_node: int):
    """
    Get the shortest route from current location to nearest exit.

    Args:
        lot_id: The ID of the parking lot.
        current_node: The current node ID.

    Returns:
        ExitRouteResponse: The shortest route details.

    Raises:
        HTTPException: If route calculation fails.
    """
    try:
        return parking_service.route_to_exit(lot_id, current_node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lot_id}/alternative-routes", response_model=AlternativeRoutesResponse)
def get_alternative_routes(lot_id: int, start: int, end: int, num_routes: int = 3):
    """
    Get multiple alternative routes between two nodes.

    Args:
        lot_id: The ID of the parking lot.
        start: The starting node ID.
        end: The ending node ID.
        num_routes: The number of alternative routes to retrieve.

    Returns:
        AlternativeRoutesResponse: Contains a list of alternative routes.

    Raises:
        HTTPException: 400 error if route calculation fails or an unexpected
                       error occurs.
    """
    try:
        return parking_service.get_alternative_routes(lot_id, start, end, num_routes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lot_id}/validate-path", response_model=PathValidationResponse)
def validate_path(
    lot_id: int, request: PathValidationRequest, db: Session = Depends(get_db)
):
    """
    Validate whether a given parking path is still available.

    Args:
        lot_id: The ID of the parking lot.
        request: The path validation request body containing node IDs.
        db: Database session dependency.

    Returns:
        PathValidationResponse: Indicates whether the path is valid and available.

    Raises:
        HTTPException: 400 error if validation fails or an unexpected error occurs.
    """
    try:
        result = parking_service.validate_path_availability(lot_id, request.node_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/nearest", response_model=LotSummary)
def get_closest_parking_lot(
    longitude: float,
    latitude: float,
    db: Session = Depends(get_db),
):
    """
    Find the closest parking lot to the given geographic coordinates.

    Args:
        longitude: Longitude of the user's current location.
        latitude: Latitude of the user's current location.
        db: Database session dependency.

    Returns:
        LotSummary: Information about the closest parking lot, including ID,
        name, location, and availability metrics.

    Raises:
        HTTPException: 404 if no parking lots exist,
                       400 for unexpected errors or invalid input.
    """
    try:
        lot = parking_service.closest_parking_lot(longitude, latitude, db)
        if not lot:
            raise HTTPException(status_code=404, detail="No parking lots available.")
        return lot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch nearest lot: {e}")


@router.get("/occupancy/hourly")
def get_occupancy_hourly(
    date: str, lot_id: int | None = None, db: Session = Depends(get_db)
):
    """
    Get hourly occupancy data for a specific date.

    Args:
        date: The date for which to retrieve occupancy data (YYYY-MM-DD).
        lot_id: Optional ID of the parking lot to filter by.
        db: Database session.

    Returns:
        Occupancy data for the specified date and lot.

    Raises:
        HTTPException: If the date format is invalid.
    """
    try:
        datetime.fromisoformat(date)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format, expected YYYY-MM-DD"
        )
    occ_repo = OccupancyRepository(db)
    return occ_repo.get_hourly_for_date(date, lot_id)


@router.get("/occupancy/daily")
def get_occupancy_daily(
    start: str, end: str, lot_id: int | None = None, db: Session = Depends(get_db)
):
    """
    Get daily occupancy data for a date range.

    Args:
        start: Start date of the range (YYYY-MM-DD).
        end: End date of the range (YYYY-MM-DD).
        lot_id: Optional ID of the parking lot to filter by.
        db: Database session.

    Returns:
        Occupancy data for the specified date range and lot.

    Raises:
        HTTPException: If the date format is invalid.
    """
    try:
        datetime.fromisoformat(start)
        datetime.fromisoformat(end)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format, expected YYYY-MM-DD"
        )
    occ_repo = OccupancyRepository(db)
    return occ_repo.get_daily_range(start, end, lot_id)


@router.get("/occupancy/monthly")
def get_occupancy_monthly(
    start: str, end: str, lot_id: int | None = None, db: Session = Depends(get_db)
):
    """
    Get monthly occupancy data for a date range.

    Args:
        start: Start date of the range (YYYY-MM-DD).
        end: End date of the range (YYYY-MM-DD).
        lot_id: Optional ID of the parking lot to filter by.
        db: Database session.

    Returns:
        Occupancy data for the specified date range and lot.

    Raises:
        HTTPException: If the date format is invalid.
    """
    try:
        datetime.fromisoformat(start)
        datetime.fromisoformat(end)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format, expected YYYY-MM-DD"
        )
    occ_repo = OccupancyRepository(db)
    return occ_repo.get_monthly_range(start, end, lot_id)
