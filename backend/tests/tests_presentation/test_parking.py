import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from presentation.routes.parking import (
    list_nodes,
    get_lot_summaries,
    get_closest_parking_lot,
    list_road_edges,
    get_route,
    update_node_status,
    find_available_spot,
    get_exit_route,
    get_alternative_routes,
    validate_path,
    get_occupancy_hourly,
    get_occupancy_daily,
    get_occupancy_monthly,
)

from application.models.parking import (
    LotSummary,
    MultiLotSummary,
    PathValidationRequest,
    SpotRecommendation,
    RouteResponse,
)


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def mock_parking_service():
    return Mock()


class TestListNodesFunction:
    """Tests for the list_nodes function."""

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_success(self, mock_parking_service, mock_db_session):
        """Test successful node listing for a parking lot."""
        mock_graph = Mock()
        mock_graph.nodes.return_value = [
            (
                1,
                {
                    "type": "PARKING_SPOT",
                    "x": 1.0,
                    "y": 1.0,
                    "status": "AVAILABLE",
                    "orientation": 90.0,
                    "label": "A1",
                },
            ),
            (2, {"type": "ROAD", "x": 2.0, "y": 2.0, "status": "AVAILABLE"}),
            (
                3,
                {
                    "type": "CAR_ENTRANCE",
                    "x": 0.0,
                    "y": 1.5,
                    "status": "AVAILABLE",
                    "label": "Entrance A",
                },
            ),
        ]

        mock_parking_service.graphs = {1: mock_graph}
        result = list_nodes(lot_id=1, db=mock_db_session)

        assert result["lot_id"] == 1
        assert "dimensions" in result
        assert "nodes" in result
        assert len(result["nodes"]) == 3

        assert result["dimensions"]["rows"] == 2  # max_y(2) - min_y(1) + 1
        assert result["dimensions"]["cols"] == 3  # max_x(2) - min_x(0) + 1

        nodes = result["nodes"]

        # First node (parking spot)
        parking_spot = next(node for node in nodes if node["id"] == 1)
        assert parking_spot["type"] == "PARKING_SPOT"
        assert parking_spot["x"] == 1.0
        assert parking_spot["y"] == 1.0
        assert parking_spot["status"] == "AVAILABLE"
        assert parking_spot["orientation"] == 90.0
        assert parking_spot["label"] == "A1"

        # Second node (road)
        road_node = next(node for node in nodes if node["id"] == 2)
        assert road_node["type"] == "ROAD"
        assert road_node["x"] == 2.0
        assert road_node["y"] == 2.0
        assert road_node["status"] == "AVAILABLE"
        assert "orientation" not in road_node
        assert "label" not in road_node

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_graph_not_found(self, mock_parking_service, mock_db_session):
        """Test node listing for non-existent parking lot."""
        # Configure parking service to not have the graph
        mock_parking_service.graphs = {}

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            list_nodes(lot_id=999, db=mock_db_session)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Graph not loaded"

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_empty_graph(self, mock_parking_service, mock_db_session):
        """Test node listing for parking lot with no nodes."""
        # Setup empty graph
        mock_graph = Mock()
        mock_graph.nodes.return_value = []
        mock_parking_service.graphs = {1: mock_graph}

        result = list_nodes(lot_id=1, db=mock_db_session)

        assert result["lot_id"] == 1
        assert result["nodes"] == []
        assert result["dimensions"]["rows"] == 0
        assert result["dimensions"]["cols"] == 0

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_missing_optional_fields(
        self, mock_parking_service, mock_db_session
    ):
        """Test node listing with nodes missing optional fields."""
        # Setup graph with missing fields
        mock_graph = Mock()
        mock_graph.nodes.return_value = [
            (
                1,
                {
                    "type": "ROAD",
                    "status": "AVAILABLE",
                    # Missing x, y, orientation, label
                },
            ),
            (
                2,
                {
                    "type": "PARKING_SPOT",
                    "x": 1.0,
                    "y": 1.0,
                    "status": "OCCUPIED",
                    # Missing orientation, label
                },
            ),
        ]
        mock_parking_service.graphs = {1: mock_graph}
        result = list_nodes(lot_id=1, db=mock_db_session)
        nodes = result["nodes"]

        # Check default values are applied
        road_node = next(node for node in nodes if node["id"] == 1)
        assert road_node["x"] == 0.0  # Default
        assert road_node["y"] == 0.0  # Default
        assert "orientation" not in road_node
        assert "label" not in road_node

        parking_node = next(node for node in nodes if node["id"] == 2)
        assert parking_node["x"] == 1.0
        assert parking_node["y"] == 1.0
        assert "orientation" not in parking_node
        assert "label" not in parking_node

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_single_node_dimensions(
        self, mock_parking_service, mock_db_session
    ):
        """Test dimensions calculation with single node."""
        mock_graph = Mock()
        mock_graph.nodes.return_value = [
            (1, {"type": "PARKING_SPOT", "x": 5.0, "y": 3.0, "status": "AVAILABLE"})
        ]
        mock_parking_service.graphs = {1: mock_graph}
        result = list_nodes(lot_id=1, db=mock_db_session)

        # Single node should result in 1x1 dimensions
        assert result["dimensions"]["rows"] == 1  # 3-3+1
        assert result["dimensions"]["cols"] == 1  # 5-5+1


class TestGetLotSummariesFunction:
    """Tests for the get_lot_summaries function."""

    @patch("presentation.routes.parking.parking_service")
    def test_get_lot_summaries_success(self, mock_parking_service, mock_db_session):
        """Test successful multi-lot summary retrieval."""
        mock_response = Mock(spec=MultiLotSummary)
        mock_response.lots_summary = [
            Mock(
                lot_id=1,
                lot_name="Downtown Lot",
                location="City Center",
                total_spots=10,
                num_occupied=4,
                num_available=6,
                occupancy_percentage=40.0,
            ),
            Mock(
                lot_id=2,
                lot_name="Mall Lot",
                location="Shopping Mall",
                total_spots=8,
                num_occupied=6,
                num_available=2,
                occupancy_percentage=75.0,
            ),
        ]

        mock_parking_service.get_lot_summaries.return_value = mock_response
        result = get_lot_summaries(db=mock_db_session)

        mock_parking_service.get_lot_summaries.assert_called_once_with(mock_db_session)

        assert result == mock_response
        assert len(result.lots_summary) == 2

        # Check first lot data
        lot1 = result.lots_summary[0]
        assert lot1.lot_id == 1
        assert lot1.lot_name == "Downtown Lot"
        assert lot1.occupancy_percentage == 40.0

        # Check second lot data
        lot2 = result.lots_summary[1]
        assert lot2.lot_id == 2
        assert lot2.occupancy_percentage == 75.0

    @patch("presentation.routes.parking.parking_service")
    def test_get_lot_summaries_empty_response(
        self, mock_parking_service, mock_db_session
    ):
        """Test multi-lot summary with no lots."""
        # Set up empty response
        mock_response = Mock(spec=MultiLotSummary)
        mock_response.lots_summary = []
        mock_parking_service.get_lot_summaries.return_value = mock_response

        result = get_lot_summaries(db=mock_db_session)

        mock_parking_service.get_lot_summaries.assert_called_once_with(mock_db_session)

        # empty result
        assert result == mock_response
        assert len(result.lots_summary) == 0

    @patch("presentation.routes.parking.parking_service")
    def test_get_lot_summaries_service_error(
        self, mock_parking_service, mock_db_session
    ):
        """Test handling of service layer errors."""
        # Configure service to raise exception
        mock_parking_service.get_lot_summaries.side_effect = Exception("Service error")

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_lot_summaries(db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Service error"

        mock_parking_service.get_lot_summaries.assert_called_once_with(mock_db_session)

    @patch("presentation.routes.parking.parking_service")
    def test_get_lot_summaries_repository_exception(
        self, mock_parking_service, mock_db_session
    ):
        """Test handling of repository-level exceptions."""
        # Configure service to raise a specific repository error
        mock_parking_service.get_lot_summaries.side_effect = ValueError(
            "Invalid lot data"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_lot_summaries(db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid lot data"

        # Verify service was called
        mock_parking_service.get_lot_summaries.assert_called_once_with(mock_db_session)

    @patch("presentation.routes.parking.parking_service")
    def test_get_lot_summaries_database_connection_error(
        self, mock_parking_service, mock_db_session
    ):
        """Test handling of database connection errors."""
        # Configure service to raise database error
        mock_parking_service.get_lot_summaries.side_effect = ConnectionError(
            "Database unavailable"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_lot_summaries(db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Database unavailable"


class TestParkingRouteFunctionsIntegration:
    """Integration-style tests for parking route functions."""

    @patch("presentation.routes.parking.parking_service")
    def test_list_nodes_complex_graph_structure(
        self, mock_parking_service, mock_db_session
    ):
        """Test list_nodes with a more complex graph structure."""
        mock_graph = Mock()
        mock_graph.nodes.return_value = [
            (1, {"type": "CAR_ENTRANCE", "x": 0.0, "y": 2.0, "status": "AVAILABLE"}),
            (2, {"type": "ROAD", "x": 1.0, "y": 2.0, "status": "AVAILABLE"}),
            (
                3,
                {
                    "type": "PARKING_SPOT",
                    "x": 1.0,
                    "y": 1.0,
                    "status": "AVAILABLE",
                    "label": "A1",
                },
            ),
            (
                4,
                {
                    "type": "PARKING_SPOT",
                    "x": 1.0,
                    "y": 3.0,
                    "status": "OCCUPIED",
                    "label": "A2",
                },
            ),
            (5, {"type": "CAR_EXIT", "x": 2.0, "y": 2.0, "status": "AVAILABLE"}),
        ]
        mock_parking_service.graphs = {1: mock_graph}

        result = list_nodes(lot_id=1, db=mock_db_session)

        node_types = [node["type"] for node in result["nodes"]]
        assert "CAR_ENTRANCE" in node_types
        assert "ROAD" in node_types
        assert "PARKING_SPOT" in node_types
        assert "CAR_EXIT" in node_types

        statuses = [node["status"] for node in result["nodes"]]
        assert "AVAILABLE" in statuses
        assert "OCCUPIED" in statuses

        assert result["dimensions"]["rows"] == 3  # y: 1, 2, 3 -> 3-1+1 = 3
        assert result["dimensions"]["cols"] == 3  # x: 0, 1, 2 -> 2-0+1 = 3

        parking_spots = [
            node for node in result["nodes"] if node["type"] == "PARKING_SPOT"
        ]
        assert len(parking_spots) == 2

        labels = [node.get("label") for node in parking_spots if "label" in node]
        assert "A1" in labels
        assert "A2" in labels


class TestGetClosestParkingLotFunction:
    """Tests for the /parking/nearest route function."""

    @patch("presentation.routes.parking.parking_service")
    def test_get_closest_parking_lot_success(
        self, mock_parking_service, mock_db_session
    ):
        """Returns 200 with a LotSummary when a closest lot exists."""
        mock_response = Mock(spec=LotSummary)
        mock_response.lot_id = 3
        mock_response.lot_name = "The Rocks"
        mock_response.location = "Sydney NSW"
        mock_response.longitude = 151.2068
        mock_response.latitude = -33.8587
        mock_response.num_available = 12
        mock_response.total_spots = 50
        mock_response.occupancy_percentage = 76.0

        mock_parking_service.closest_parking_lot.return_value = mock_response

        result = get_closest_parking_lot(
            longitude=151.2093, latitude=-33.8688, db=mock_db_session
        )

        mock_parking_service.closest_parking_lot.assert_called_once_with(
            151.2093, -33.8688, mock_db_session
        )
        assert result is mock_response
        assert result.lot_id == 3
        assert result.lot_name == "The Rocks"

    @patch("presentation.routes.parking.parking_service")
    def test_get_closest_parking_lot_not_found(
        self, mock_parking_service, mock_db_session
    ):
        """When service returns None, route raises 404."""
        mock_parking_service.closest_parking_lot.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_closest_parking_lot(longitude=151.0, latitude=-33.8, db=mock_db_session)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "No parking lots available."
        mock_parking_service.closest_parking_lot.assert_called_once_with(
            151.0, -33.8, mock_db_session
        )

    @patch("presentation.routes.parking.parking_service")
    def test_get_closest_parking_lot_service_error(
        self, mock_parking_service, mock_db_session
    ):
        """Unhandled service exception is surfaced as 400 with message."""
        mock_parking_service.closest_parking_lot.side_effect = Exception(
            "Service error"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_closest_parking_lot(longitude=151.2, latitude=-33.9, db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail.startswith(
            "Failed to fetch nearest lot: Service error"
        )
        mock_parking_service.closest_parking_lot.assert_called_once_with(
            151.2, -33.9, mock_db_session
        )

    @patch("presentation.routes.parking.parking_service")
    def test_get_closest_parking_lot_parameter_passthrough(
        self, mock_parking_service, mock_db_session
    ):
        """Ensures the route passes longitude/latitude/db to the service exactly."""
        mock_parking_service.closest_parking_lot.return_value = Mock(spec=LotSummary)

        lon, lat = 151.1234, -33.9876
        _ = get_closest_parking_lot(longitude=lon, latitude=lat, db=mock_db_session)

        mock_parking_service.closest_parking_lot.assert_called_once_with(
            lon, lat, mock_db_session
        )


class TestParkingEdgesAndRoutes:
    """Tests for edges and routing functions."""

    @patch("presentation.routes.parking.parking_service")
    def test_list_road_edges_success(self, mock_parking_service, mock_db_session):
        """Test successful retrieval of road edges."""
        mock_edges = [Mock(edge_id=1, source=1, target=2)]
        mock_parking_service.get_road_edges.return_value = mock_edges

        result = list_road_edges(lot_id=1, db=mock_db_session)

        assert result == mock_edges
        mock_parking_service.get_road_edges.assert_called_once_with(1)

    @patch("presentation.routes.parking.parking_service")
    def test_list_road_edges_failure(self, mock_parking_service, mock_db_session):
        """Test error handling when retrieving road edges."""
        mock_parking_service.get_road_edges.side_effect = Exception("Graph error")

        with pytest.raises(HTTPException) as exc_info:
            list_road_edges(lot_id=1, db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Graph error"

    @patch("presentation.routes.parking.parking_service")
    def test_get_route_success(self, mock_parking_service):
        """Test successful shortest route calculation."""
        mock_route = Mock(spec=RouteResponse)
        mock_parking_service.shortest_path.return_value = mock_route

        result = get_route(lot_id=1, start=10, end=20)

        assert result == mock_route
        mock_parking_service.shortest_path.assert_called_once_with(1, 10, 20)

    @patch("presentation.routes.parking.parking_service")
    def test_get_route_failure(self, mock_parking_service):
        """Test error handling for route calculation."""
        mock_parking_service.shortest_path.side_effect = Exception("No path found")

        with pytest.raises(HTTPException) as exc_info:
            get_route(lot_id=1, start=10, end=20)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No path found"

    @patch("presentation.routes.parking.parking_service")
    def test_get_exit_route(self, mock_parking_service):
        """Test retrieval of route to nearest exit."""
        mock_response = Mock()
        mock_parking_service.route_to_exit.return_value = mock_response

        result = get_exit_route(lot_id=1, current_node=5)

        assert result == mock_response
        mock_parking_service.route_to_exit.assert_called_once_with(1, 5)

    @patch("presentation.routes.parking.parking_service")
    def test_get_alternative_routes(self, mock_parking_service):
        """Test retrieval of alternative routes."""
        mock_response = Mock()
        mock_parking_service.get_alternative_routes.return_value = mock_response

        result = get_alternative_routes(lot_id=1, start=1, end=2, num_routes=2)

        assert result == mock_response
        mock_parking_service.get_alternative_routes.assert_called_once_with(1, 1, 2, 2)


class TestNodeStatusUpdates:
    """Tests for async node status updates."""

    @pytest.mark.asyncio
    @patch("presentation.routes.parking.parking_service")
    async def test_update_node_status_success(
        self, mock_parking_service, mock_db_session
    ):
        """Test successful async node status update."""
        # Setup async mock
        mock_parking_service.update_node_status = AsyncMock(
            return_value={"success": True}
        )

        result = await update_node_status(
            lot_id=1, node_id=10, status="OCCUPIED", ttl=3600, db=mock_db_session
        )

        assert result == {"success": True}
        mock_parking_service.update_node_status.assert_awaited_once_with(
            1, 10, "OCCUPIED", 3600, mock_db_session
        )

    @pytest.mark.asyncio
    @patch("presentation.routes.parking.parking_service")
    async def test_update_node_status_http_exception(
        self, mock_parking_service, mock_db_session
    ):
        """Test that HTTPExceptions from service are re-raised correctly."""
        mock_parking_service.update_node_status = AsyncMock(
            side_effect=HTTPException(status_code=403, detail="Forbidden")
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_node_status(1, 10, "OCCUPIED", 3600, mock_db_session)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Forbidden"

    @pytest.mark.asyncio
    @patch("presentation.routes.parking.parking_service")
    async def test_update_node_status_generic_exception(
        self, mock_parking_service, mock_db_session
    ):
        """Test that generic exceptions result in 500 error."""
        mock_parking_service.update_node_status = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_node_status(1, 10, "OCCUPIED", 3600, mock_db_session)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unexpected error"


class TestSpotFindingAndValidation:
    """Tests for finding spots and validating paths."""

    @patch("presentation.routes.parking.parking_service")
    def test_find_available_spot_success(self, mock_parking_service, mock_db_session):
        """Test finding a spot with orientation preference."""
        mock_spot = Mock(spec=SpotRecommendation)
        mock_parking_service.find_nearest_available_spot.return_value = mock_spot

        result = find_available_spot(
            lot_id=1, entrance_id=5, orientation=90.0, db=mock_db_session
        )

        assert result == mock_spot
        mock_parking_service.find_nearest_available_spot.assert_called_once_with(
            1, 5, {"orientation": 90.0}
        )

    @patch("presentation.routes.parking.parking_service")
    def test_find_available_spot_not_found(self, mock_parking_service, mock_db_session):
        """Test 404 raised when no spot is returned."""
        mock_parking_service.find_nearest_available_spot.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            find_available_spot(lot_id=1, entrance_id=5, db=mock_db_session)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "No available spots found"

    @patch("presentation.routes.parking.parking_service")
    def test_validate_path_success(self, mock_parking_service, mock_db_session):
        """Test path validation."""
        mock_response = Mock()
        mock_parking_service.validate_path_availability.return_value = mock_response

        request = PathValidationRequest(node_ids=[1, 2, 3])
        result = validate_path(lot_id=1, request=request, db=mock_db_session)

        assert result == mock_response
        mock_parking_service.validate_path_availability.assert_called_once_with(
            1, [1, 2, 3]
        )

    @patch("presentation.routes.parking.parking_service")
    def test_validate_path_error(self, mock_parking_service, mock_db_session):
        """Test path validation error handling."""
        mock_parking_service.validate_path_availability.side_effect = Exception(
            "Validation failed"
        )

        request = PathValidationRequest(node_ids=[1, 2])
        with pytest.raises(HTTPException) as exc_info:
            validate_path(lot_id=1, request=request, db=mock_db_session)

        assert exc_info.value.status_code == 400


class TestOccupancyRoutes:
    """Tests for occupancy statistics endpoints."""

    @patch("presentation.routes.parking.OccupancyRepository")
    def test_get_occupancy_hourly_success(self, mock_repo_cls, mock_db_session):
        """Test hourly occupancy retrieval with valid date."""
        mock_repo_instance = mock_repo_cls.return_value
        mock_repo_instance.get_hourly_for_date.return_value = {"data": []}

        result = get_occupancy_hourly(date="2023-10-25", lot_id=1, db=mock_db_session)

        assert result == {"data": []}
        mock_repo_cls.assert_called_once_with(mock_db_session)
        mock_repo_instance.get_hourly_for_date.assert_called_once_with("2023-10-25", 1)

    def test_get_occupancy_hourly_invalid_date(self, mock_db_session):
        """Test hourly occupancy with invalid date format."""
        with pytest.raises(HTTPException) as exc_info:
            get_occupancy_hourly(date="invalid-date", lot_id=1, db=mock_db_session)

        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    @patch("presentation.routes.parking.OccupancyRepository")
    def test_get_occupancy_daily_success(self, mock_repo_cls, mock_db_session):
        """Test daily occupancy range retrieval."""
        mock_repo_instance = mock_repo_cls.return_value
        mock_repo_instance.get_daily_range.return_value = {"data": []}

        result = get_occupancy_daily(
            start="2023-10-01", end="2023-10-05", lot_id=1, db=mock_db_session
        )

        assert result == {"data": []}
        mock_repo_instance.get_daily_range.assert_called_once_with(
            "2023-10-01", "2023-10-05", 1
        )

    def test_get_occupancy_daily_invalid_date(self, mock_db_session):
        """Test daily occupancy with invalid date format."""
        with pytest.raises(HTTPException) as exc_info:
            get_occupancy_daily(
                start="2023-10-01", end="not-a-date", db=mock_db_session
            )

        assert exc_info.value.status_code == 400

    @patch("presentation.routes.parking.OccupancyRepository")
    def test_get_occupancy_monthly_success(self, mock_repo_cls, mock_db_session):
        """Test monthly occupancy range retrieval."""
        mock_repo_instance = mock_repo_cls.return_value
        mock_repo_instance.get_monthly_range.return_value = {"data": []}

        result = get_occupancy_monthly(
            start="2023-01-01", end="2023-06-01", lot_id=1, db=mock_db_session
        )

        assert result == {"data": []}
        mock_repo_instance.get_monthly_range.assert_called_once_with(
            "2023-01-01", "2023-06-01", 1
        )

    def test_get_occupancy_monthly_invalid_date(self, mock_db_session):
        """Test monthly occupancy with invalid date format."""
        with pytest.raises(HTTPException) as exc_info:
            get_occupancy_monthly(
                start="bad-date", end="2023-06-01", db=mock_db_session
            )

        assert exc_info.value.status_code == 400
