import pytest
import asyncio
import networkx as nx
from unittest.mock import Mock, patch
from types import SimpleNamespace
from datetime import datetime, timedelta
from fastapi import HTTPException
from application.services.parking_service import ParkingService, _get
from application.models.parking import MultiLotSummary
from database.models.parking import NodeStatus


@pytest.fixture
def mock_parking_repository():
    return Mock()


@pytest.fixture
def mock_occupancy_repository():
    return Mock()


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def parking_service():
    return ParkingService()


def test_get_helper():
    """Test the _get helper function for both objects and dicts."""
    d = {"a": 1, "b": 2}
    assert _get(d, "a") == 1
    assert _get(d, "c", 3) == 3

    o = SimpleNamespace(x=10, y=20)
    assert _get(o, "x") == 10
    assert _get(o, "z", 30) == 30


def test_build_graph(parking_service):
    """Test building a graph from nodes and edges."""
    type_road = SimpleNamespace(value="ROAD")
    status_open = SimpleNamespace(value="OPEN")

    nodes = [
        {
            "id": 1,
            "lot_id": 100,
            "x": 0,
            "y": 0,
            "type": type_road,
            "status": status_open,
            "label": "A",
        },
        SimpleNamespace(
            id=2, lot_id=100, x=10, y=0, type=type_road, status=status_open, label="B"
        ),
    ]

    edges = [
        {
            "from_node_id": 1,
            "to_node_id": 2,
            "length_m": 10.0,
            "bidirectional": True,
            "status": "OPEN",
        }
    ]

    parking_service.build_graph(100, nodes, edges)

    G = parking_service.graphs[100]
    assert len(G.nodes) == 2
    assert len(G.edges) == 2
    assert G.nodes[1]["x"] == 0.0
    assert G.edges[1, 2]["weight"] == 10.0


def test_get_road_edges_success(parking_service):
    """Test retrieving sorted road edges."""
    G = nx.DiGraph()
    G.add_node(1, type="ROAD", x=0, y=0)
    G.add_node(2, type="ROAD", x=10, y=0)
    G.add_node(3, type="ROAD", x=0, y=10)
    G.add_node(4, type="PARKING_SPOT", x=5, y=5)

    G.add_edge(1, 2, length=10, weight=10, status="OPEN", bidirectional=True)
    G.add_edge(1, 3, length=10, weight=10, status="OPEN", bidirectional=True)
    G.add_edge(2, 4, length=5, weight=5, status="OPEN", bidirectional=False)

    parking_service.graphs[1] = G

    edges = parking_service.get_road_edges(1)

    assert len(edges) == 2
    assert edges[0]["to_node_id"] == 2
    assert edges[1]["to_node_id"] == 3


def test_get_road_edges_not_found(parking_service):
    with pytest.raises(HTTPException) as exc:
        parking_service.get_road_edges(999)
    assert exc.value.status_code == 404


def test_shortest_path_success(parking_service):
    G = nx.DiGraph()
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=10, y=0)
    G.add_edge(1, 2, length=10, weight=10)
    parking_service.graphs[1] = G

    result = parking_service.shortest_path(1, 1, 2)
    assert result["node_ids"] == [1, 2]
    assert result["total_distance_m"] == 10


def test_shortest_path_errors(parking_service):
    with pytest.raises(ValueError, match="Graph not loaded"):
        parking_service.shortest_path(1, 1, 2)

    G = nx.DiGraph()
    G.add_node(1)
    parking_service.graphs[1] = G
    with pytest.raises(ValueError, match="Start or end node not in graph"):
        parking_service.shortest_path(1, 1, 99)


def test_route_to_exit(parking_service):
    G = nx.DiGraph()
    G.add_node(1, type="ROAD", x=0, y=0)
    G.add_node(2, type="CAR_EXIT", x=10, y=0)
    G.add_node(3, type="CAR_EXIT", x=0, y=10)

    G.add_edge(1, 2, length=10, weight=10, status="OPEN")
    G.add_edge(1, 3, length=2, weight=2, status="CLOSED")

    parking_service.graphs[1] = G

    result = parking_service.route_to_exit(1, 1)
    assert result["exit_node_id"] == 2
    assert result["total_distance_m"] == 10


def test_route_to_exit_no_exits(parking_service):
    G = nx.DiGraph()
    G.add_node(1, type="ROAD")
    parking_service.graphs[1] = G
    with pytest.raises(ValueError, match="No exits found"):
        parking_service.route_to_exit(1, 1)


def test_route_to_exit_no_path(parking_service):
    G = nx.DiGraph()
    G.add_node(1, type="ROAD", x=0, y=0)
    G.add_node(2, type="CAR_EXIT", x=10, y=0)
    parking_service.graphs[1] = G
    with pytest.raises(ValueError, match="No path to exit found"):
        parking_service.route_to_exit(1, 1)


def test_find_nearest_available_spot(parking_service):
    G = nx.DiGraph()
    G.add_node(1, type="ENTRANCE", x=0, y=0)

    G.add_node(2, type="PARKING_SPOT", status="OCCUPIED", x=10, y=0)
    G.add_edge(1, 2, length=10, weight=10, status="OPEN")

    G.add_node(
        3,
        type="PARKING_SPOT",
        status="AVAILABLE",
        x=20,
        y=0,
        label="Spot 2",
        orientation=90,
    )
    G.add_edge(1, 3, length=20, weight=20, status="OPEN")

    G.add_node(4, type="PARKING_SPOT", status="AVAILABLE", x=5, y=0)
    G.add_edge(1, 4, length=5, weight=5, status="CLOSED")

    parking_service.graphs[1] = G

    res = parking_service.find_nearest_available_spot(1, 1)
    assert res["spot_node_id"] == 3
    assert res["spot_label"] == "Spot 2"

    res_pref_match = parking_service.find_nearest_available_spot(
        1, 1, spot_preferences={"orientation": 90}
    )
    assert res_pref_match["spot_node_id"] == 3


def test_find_nearest_available_spot_none(parking_service):
    G = nx.DiGraph()
    G.add_node(1, type="ENTRANCE")
    parking_service.graphs[1] = G
    assert parking_service.find_nearest_available_spot(1, 1) is None


def test_get_alternative_routes(parking_service):
    G = nx.DiGraph()
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=10, y=0)

    G.add_edge(1, 2, length=10, weight=10, status="OPEN")

    G.add_node(3, x=5, y=5)
    G.add_edge(1, 3, length=10, weight=10, status="OPEN")
    G.add_edge(3, 2, length=10, weight=10, status="OPEN")

    parking_service.graphs[1] = G

    res = parking_service.get_alternative_routes(1, 1, 2, num_routes=2)
    assert len(res["routes"]) == 2
    assert res["routes"][0]["total_distance_m"] == 10
    assert res["routes"][1]["total_distance_m"] == 20


def test_get_alternative_routes_no_path(parking_service):
    G = nx.DiGraph()
    G.add_node(1)
    G.add_node(2)
    parking_service.graphs[1] = G
    with pytest.raises(ValueError, match="Graph not loaded"):
        parking_service.get_alternative_routes(99, 1, 2)

    with pytest.raises(ValueError, match="No path exists"):
        parking_service.get_alternative_routes(1, 1, 2)


def test_validate_path_availability(parking_service):
    G = nx.DiGraph()
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=10, y=0)
    G.add_node(3, type="PARKING_SPOT", status="OCCUPIED", x=20, y=0)
    G.add_edge(1, 2, status="CLOSED")

    parking_service.graphs[1] = G

    assert parking_service.validate_path_availability(99, [1])["valid"] is False
    assert parking_service.validate_path_availability(1, [1, 99])["valid"] is False
    assert parking_service.validate_path_availability(1, [2, 3])["valid"] is False

    res_blocked = parking_service.validate_path_availability(1, [1, 2])
    assert res_blocked["valid"] is False
    assert "Path blocked" in res_blocked["reason"]

    G.add_edge(2, 3, status="OPEN")
    res_dest = parking_service.validate_path_availability(1, [2, 3])
    assert res_dest["valid"] is False
    assert "Destination spot is OCCUPIED" in res_dest["reason"]


@patch("application.services.parking_service.ParkingRepository")
@patch("application.services.parking_service.OccupancyRepository")
@patch("application.services.parking_service.schedule_ttl_reset")
@patch("application.services.parking_service.broadcast_event")
def test_update_node_status_transitions(
    mock_broadcast,
    mock_schedule,
    mock_occ_repo_class,
    mock_park_repo_class,
    mock_db_session,
    parking_service,
):
    async def run_test():
        mock_repo = mock_park_repo_class.return_value
        mock_occ_repo = mock_occ_repo_class.return_value

        G = nx.DiGraph()
        G.add_node(1, status="AVAILABLE")
        parking_service.graphs[100] = G

        mock_node = Mock()
        mock_node.id = 1
        mock_node.status = NodeStatus.AVAILABLE
        mock_node.expires_at = None
        mock_repo.get_node.return_value = mock_node

        # Available -> Reserved
        res = await parking_service.update_node_status(
            100, 1, "RESERVED", 300, mock_db_session
        )
        assert res["status"] == "RESERVED"
        assert mock_node.status == NodeStatus.RESERVED
        assert mock_schedule.called
        assert G.nodes[1]["status"] == "RESERVED"

        # Reserved -> Occupied
        mock_node.status = NodeStatus.RESERVED
        res = await parking_service.update_node_status(
            100, 1, "OCCUPIED", 300, mock_db_session
        )
        assert res["status"] == "OCCUPIED"
        assert mock_node.status == NodeStatus.OCCUPIED
        assert mock_occ_repo.record_occupancy.called

        # Occupied -> Available
        mock_node.status = NodeStatus.OCCUPIED
        res = await parking_service.update_node_status(
            100, 1, "AVAILABLE", 300, mock_db_session
        )
        assert res["status"] == "AVAILABLE"
        assert mock_broadcast.called

    asyncio.run(run_test())


@patch("application.services.parking_service.ParkingRepository")
def test_update_node_status_errors(mock_repo_class, mock_db_session, parking_service):
    async def run_test():
        mock_repo = mock_repo_class.return_value

        # 404 Node Not Found
        mock_repo.get_node.return_value = None
        with pytest.raises(HTTPException) as exc:
            await parking_service.update_node_status(
                1, 1, "RESERVED", 60, mock_db_session
            )
        assert exc.value.status_code == 404

        # 400 Invalid Status
        mock_node = Mock(status=NodeStatus.AVAILABLE)
        mock_repo.get_node.return_value = mock_node
        with pytest.raises(HTTPException) as exc:
            await parking_service.update_node_status(
                1, 1, "INVALID_STATE", 60, mock_db_session
            )
        assert exc.value.status_code == 400

        # 409 Conflict: Reserve Occupied
        mock_node.status = NodeStatus.OCCUPIED
        with pytest.raises(HTTPException) as exc:
            await parking_service.update_node_status(
                1, 1, "RESERVED", 60, mock_db_session
            )
        assert exc.value.status_code == 409

        # 409 Conflict: Occupy Available
        mock_node.status = NodeStatus.AVAILABLE
        with pytest.raises(HTTPException) as exc:
            await parking_service.update_node_status(
                1, 1, "OCCUPIED", 60, mock_db_session
            )
        assert exc.value.status_code == 409

        # 409 Conflict: Free Reserved
        mock_node.status = NodeStatus.RESERVED
        with pytest.raises(HTTPException) as exc:
            await parking_service.update_node_status(
                1, 1, "AVAILABLE", 60, mock_db_session
            )
        assert exc.value.status_code == 409

    asyncio.run(run_test())


@patch("application.services.parking_service.ParkingRepository")
@patch("application.services.parking_service.schedule_ttl_reset")
@patch("application.services.parking_service.broadcast_event")
def test_update_node_status_reserved_extension(
    mock_broadcast, mock_schedule, mock_repo_class, mock_db_session, parking_service
):
    async def run_test():
        mock_repo = mock_repo_class.return_value
        mock_node = Mock()
        mock_node.id = 1
        mock_node.status = NodeStatus.RESERVED
        mock_node.expires_at = datetime.utcnow() - timedelta(seconds=10)
        mock_repo.get_node.return_value = mock_node

        res = await parking_service.update_node_status(
            100, 1, "RESERVED", 300, mock_db_session
        )
        assert res["status"] == "RESERVED"
        assert mock_schedule.called

    asyncio.run(run_test())


def lot(i, name, lon, lat, location=""):
    return SimpleNamespace(
        id=i, name=name, longitude=lon, latitude=lat, location=location
    )


@patch("application.services.parking_service.ParkingRepository")
def test_get_lot_summaries_success(
    mock_repo_class, mock_parking_repository, mock_db_session
):
    mock_repo_class.return_value = mock_parking_repository
    mock_lot1 = Mock()
    mock_lot1.id = 1
    mock_lot1.name = "Downtown Lot"
    mock_lot1.location = "City Center"
    mock_lot1.longitude = 151.2069
    mock_lot1.latitude = -33.8726

    mock_lot2 = Mock()
    mock_lot2.id = 2
    mock_lot2.name = "Mall Lot"
    mock_lot2.location = "Shopping Mall"
    mock_lot2.longitude = 151.0090
    mock_lot2.latitude = -33.8000

    mock_parking_repository.get_all_lots.return_value = [mock_lot1, mock_lot2]
    mock_parking_repository.count_spots.side_effect = lambda lot_id: (
        10 if lot_id == 1 else 8
    )
    mock_parking_repository.count_occupied_spots.side_effect = lambda lot_id: (
        4 if lot_id == 1 else 6
    )
    mock_parking_repository.count_vacant_spots.side_effect = lambda lot_id: (
        6 if lot_id == 1 else 2
    )
    mock_parking_repository.get_occupancy_percentage.side_effect = lambda lot_id: (
        40.0 if lot_id == 1 else 75.0
    )

    service = ParkingService()
    result = service.get_lot_summaries(mock_db_session)
    assert isinstance(result, MultiLotSummary)
    assert len(result.lots_summary) == 2


@patch("application.services.parking_service.ParkingRepository")
def test_get_lot_summaries_empty_database(
    mock_repo_class, mock_parking_repository, mock_db_session
):
    mock_repo_class.return_value = mock_parking_repository
    mock_parking_repository.get_all_lots.return_value = []
    service = ParkingService()
    result = service.get_lot_summaries(mock_db_session)
    assert result.lots_summary == []


@patch("application.services.parking_service.ParkingRepository")
def test_get_lot_summaries_repository_exception(
    mock_repo_class, mock_parking_repository, mock_db_session
):
    mock_repo_class.return_value = mock_parking_repository
    mock_parking_repository.get_all_lots.side_effect = Exception("Database error")
    service = ParkingService()
    with pytest.raises(Exception) as exc_info:
        service.get_lot_summaries(mock_db_session)
    assert "Database error" in str(exc_info.value)


@patch("application.services.parking_service.ParkingRepository")
def test_closest_parking_lot_picks_nearest(
    mock_repo_class, mock_parking_repository, mock_db_session
):
    mock_repo_class.return_value = mock_parking_repository
    qvb = lot(1, "QVB", 151.2069, -33.8726)
    bondi = lot(2, "Bondi", 151.2743, -33.8915)
    mock_parking_repository.get_all_lots.return_value = [bondi, qvb]

    mock_parking_repository.count_spots.return_value = 100
    mock_parking_repository.count_occupied_spots.return_value = 30
    mock_parking_repository.count_vacant_spots.return_value = 70
    mock_parking_repository.get_occupancy_percentage.return_value = 30.0

    res = ParkingService().closest_parking_lot(151.2065, -33.8730, mock_db_session)
    assert res.lot_id == qvb.id


@patch("application.services.parking_service.ParkingRepository")
def test_closest_parking_lot_no_lots_returns_none(
    mock_repo_class, mock_parking_repository, mock_db_session
):
    mock_repo_class.return_value = mock_parking_repository
    mock_parking_repository.get_all_lots.return_value = []
    res = ParkingService().closest_parking_lot(151.0, -33.8, mock_db_session)
    assert res is None
