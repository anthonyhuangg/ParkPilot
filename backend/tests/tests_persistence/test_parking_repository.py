import pytest
from persistence.parking_repository import ParkingRepository
from database.models.parking import Base, NodeStatus, NodeType
from database.parking_database import LotDatabase, NodeDatabase, EdgeDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def parking_repository(db_session):
    return ParkingRepository(db_session)


@pytest.fixture
def sample_lots_with_nodes_and_edges(db_session):
    lot_db = LotDatabase(db_session)
    node_db = NodeDatabase(db_session)
    edge_db = EdgeDatabase(db_session)

    lot1 = lot_db.create_lot(
        {
            "name": "Downtown Lot",
            "longitude": 151.2,
            "latitude": -33.9,
            "location": "City Center",
        }
    )
    lot2 = lot_db.create_lot(
        {
            "name": "Mall Lot",
            "longitude": 151.3,
            "latitude": -33.8,
            "location": "Shopping Mall",
        }
    )

    # Lot 1: 5 parking spots (3 available, 2 occupied) + 1 road
    nodes_lot1 = []
    for i in range(5):
        status = NodeStatus.AVAILABLE if i < 3 else NodeStatus.OCCUPIED
        node = node_db.create_node(
            {
                "lot_id": lot1.id,
                "type": NodeType.PARKING_SPOT,
                "x": i,
                "y": 1,
                "status": status,
                "label": f"A{i + 1}",
            }
        )
        nodes_lot1.append(node)

    road_node1 = node_db.create_node(
        {
            "lot_id": lot1.id,
            "type": NodeType.ROAD,
            "x": 2,
            "y": 2,
            "status": NodeStatus.AVAILABLE,
        }
    )
    nodes_lot1.append(road_node1)

    # Lot 2: 4 parking spots (1 available, 3 occupied) + 2 roads
    nodes_lot2 = []
    for i in range(4):
        status = NodeStatus.AVAILABLE if i == 0 else NodeStatus.OCCUPIED
        node = node_db.create_node(
            {
                "lot_id": lot2.id,
                "type": NodeType.PARKING_SPOT,
                "x": i,
                "y": 2,
                "status": status,
                "label": f"B{i + 1}",
            }
        )
        nodes_lot2.append(node)

    for i in range(2):
        road_node = node_db.create_node(
            {
                "lot_id": lot2.id,
                "type": NodeType.ROAD,
                "x": i,
                "y": 3,
                "status": NodeStatus.AVAILABLE,
            }
        )
        nodes_lot2.append(road_node)

    edges_lot1 = []
    for i in range(2):
        edge = edge_db.create_edge(
            {
                "lot_id": lot1.id,
                "from_node_id": nodes_lot1[i].id,
                "to_node_id": nodes_lot1[i + 1].id,
                "length_m": 5.0,
                "weight": 1.0,
            }
        )
        edges_lot1.append(edge)

    edges_lot2 = []
    edge = edge_db.create_edge(
        {
            "lot_id": lot2.id,
            "from_node_id": nodes_lot2[0].id,
            "to_node_id": nodes_lot2[1].id,
            "length_m": 3.0,
            "weight": 1.5,
        }
    )
    edges_lot2.append(edge)

    return lot1, lot2, nodes_lot1, nodes_lot2, edges_lot1, edges_lot2


def test_count_spots(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, _, _ = sample_lots_with_nodes_and_edges

    assert parking_repository.count_spots(lot1.id) == 5
    assert parking_repository.count_spots(lot2.id) == 4
    assert parking_repository.count_spots(999) == 0


def test_count_occupied_spots(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, _, _ = sample_lots_with_nodes_and_edges

    assert parking_repository.count_occupied_spots(lot1.id) == 2
    assert parking_repository.count_occupied_spots(lot2.id) == 3
    assert parking_repository.count_occupied_spots(999) == 0


def test_count_vacant_spots(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, _, _ = sample_lots_with_nodes_and_edges

    assert parking_repository.count_vacant_spots(lot1.id) == 3
    assert parking_repository.count_vacant_spots(lot2.id) == 1
    assert parking_repository.count_vacant_spots(999) == 0


def test_get_occupancy_percentage(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, _, _ = sample_lots_with_nodes_and_edges

    assert parking_repository.get_occupancy_percentage(lot1.id) == 40.0
    assert parking_repository.get_occupancy_percentage(lot2.id) == 75.0
    assert parking_repository.get_occupancy_percentage(999) == 0.0


def test_get_occupancy_percentage_no_spots(parking_repository, db_session):
    lot_db = LotDatabase(db_session)
    lot_no_spots = lot_db.create_lot(
        {"name": "Empty Lot", "longitude": 151.1, "latitude": -33.7}
    )

    assert parking_repository.get_occupancy_percentage(lot_no_spots.id) == 0.0


def test_get_all_lots(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, _, _ = sample_lots_with_nodes_and_edges

    all_lots = parking_repository.get_all_lots()
    assert len(all_lots) == 2

    lot_names = [lot.name for lot in all_lots]
    assert "Downtown Lot" in lot_names
    assert "Mall Lot" in lot_names


def test_get_all_lots_empty_database(parking_repository):
    """Test get_all_lots when database is empty."""
    all_lots = parking_repository.get_all_lots()
    assert len(all_lots) == 0
    assert all_lots == []


def test_get_all_nodes_for_lot(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, nodes_lot1, nodes_lot2, _, _ = sample_lots_with_nodes_and_edges

    # Test lot 1 nodes (5 parking spots + 1 road)
    lot1_nodes = parking_repository.get_all_nodes_for_lot(lot1.id)
    assert len(lot1_nodes) == 6

    for node in lot1_nodes:
        assert hasattr(node, "id")
        assert hasattr(node, "type")
        assert hasattr(node, "status")

    # Test lot 2 nodes (4 parking spots + 2 roads)
    lot2_nodes = parking_repository.get_all_nodes_for_lot(lot2.id)
    assert len(lot2_nodes) == 6

    # Test non-existent lot
    no_nodes = parking_repository.get_all_nodes_for_lot(999)
    assert len(no_nodes) == 0


def test_get_all_nodes_for_lot_empty_lot(parking_repository, db_session):
    lot_db = LotDatabase(db_session)
    empty_lot = lot_db.create_lot(
        {"name": "Empty Lot", "longitude": 151.1, "latitude": -33.7}
    )

    nodes = parking_repository.get_all_nodes_for_lot(empty_lot.id)
    assert len(nodes) == 0
    assert nodes == []


def test_get_node_success(parking_repository, sample_lots_with_nodes_and_edges):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges
    target_node = nodes_lot1[0]
    retrieved_node = parking_repository.get_node(target_node.id)

    assert retrieved_node is not None
    assert retrieved_node.id == target_node.id
    assert retrieved_node.type == target_node.type
    assert retrieved_node.status == target_node.status


def test_get_node_not_found(parking_repository):
    result = parking_repository.get_node(999)
    assert result is None


def test_get_node_different_types(parking_repository, sample_lots_with_nodes_and_edges):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges

    parking_spot = parking_repository.get_node(nodes_lot1[0].id)
    assert parking_spot.type == NodeType.PARKING_SPOT

    road_node = parking_repository.get_node(nodes_lot1[-1].id)
    assert road_node.type == NodeType.ROAD


def test_update_node_status_success(
    parking_repository, sample_lots_with_nodes_and_edges
):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges

    node_to_update = nodes_lot1[0]  # First parking spot (should be AVAILABLE)
    original_status = node_to_update.status

    updated_node = parking_repository.update_node_status(
        node_to_update.id, NodeStatus.OCCUPIED
    )

    assert updated_node is not None
    assert updated_node.id == node_to_update.id
    assert updated_node.status == NodeStatus.OCCUPIED.value
    assert updated_node.status != original_status


def test_update_node_status_invalid_node(parking_repository):
    result = parking_repository.update_node_status(999, NodeStatus.OCCUPIED)
    assert result is None


def test_update_node_status_various_statuses(
    parking_repository, sample_lots_with_nodes_and_edges
):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges
    node_to_update = nodes_lot1[1]

    # Test updating to OCCUPIED
    updated = parking_repository.update_node_status(
        node_to_update.id, NodeStatus.OCCUPIED
    )
    assert updated.status == NodeStatus.OCCUPIED.value

    # Test updating back to AVAILABLE
    updated = parking_repository.update_node_status(
        node_to_update.id, NodeStatus.AVAILABLE
    )
    assert updated.status == NodeStatus.AVAILABLE.value


def test_save_node_changes(parking_repository, sample_lots_with_nodes_and_edges):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges

    node = parking_repository.get_node(nodes_lot1[0].id)
    original_status = node.status

    new_status = (
        NodeStatus.OCCUPIED
        if original_status == NodeStatus.AVAILABLE
        else NodeStatus.AVAILABLE
    )
    node.status = new_status

    parking_repository.save(node)

    retrieved_node = parking_repository.get_node(node.id)
    assert retrieved_node.status == new_status
    assert retrieved_node.status != original_status


def test_save_preserves_other_attributes(
    parking_repository, sample_lots_with_nodes_and_edges
):
    _, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges

    node = parking_repository.get_node(nodes_lot1[0].id)
    original_x = node.x
    original_y = node.y
    original_type = node.type

    node.status = NodeStatus.OCCUPIED
    parking_repository.save(node)

    retrieved_node = parking_repository.get_node(node.id)
    assert retrieved_node.x == original_x
    assert retrieved_node.y == original_y
    assert retrieved_node.type == original_type
    assert retrieved_node.status == NodeStatus.OCCUPIED


def test_edges_exist_for_lot(parking_repository, sample_lots_with_nodes_and_edges):
    lot1, lot2, _, _, edges_lot1, edges_lot2 = sample_lots_with_nodes_and_edges

    lot1_edges_raw = parking_repository.edge_db.get_all_edges_for_lot(lot1.id)
    assert len(lot1_edges_raw) == 2

    lot2_edges_raw = parking_repository.edge_db.get_all_edges_for_lot(lot2.id)
    assert len(lot2_edges_raw) == 1

    for edge in lot1_edges_raw:
        assert edge.id is not None
        assert edge.from_node_id is not None
        assert edge.to_node_id is not None
        assert edge.length_m == 5.0
        assert edge.weight == 1.0

    for edge in lot2_edges_raw:
        assert edge.id is not None
        assert edge.from_node_id is not None
        assert edge.to_node_id is not None
        assert edge.length_m == 3.0
        assert edge.weight == 1.5


def test_get_all_edges_for_lot_empty_lot(parking_repository, db_session):
    lot_db = LotDatabase(db_session)
    empty_lot = lot_db.create_lot(
        {"name": "Empty Lot", "longitude": 151.1, "latitude": -33.7}
    )

    edges = parking_repository.get_all_edges_for_lot(empty_lot.id)
    assert len(edges) == 0
    assert edges == []


def test_repository_workflow_integration(
    parking_repository, sample_lots_with_nodes_and_edges
):
    lot1, _, nodes_lot1, _, _, _ = sample_lots_with_nodes_and_edges

    all_nodes = parking_repository.get_all_nodes_for_lot(lot1.id)
    assert len(all_nodes) == 6  # 5 parking spots + 1 road

    total_spots = parking_repository.count_spots(lot1.id)
    initial_occupied = parking_repository.count_occupied_spots(lot1.id)
    initial_vacant = parking_repository.count_vacant_spots(lot1.id)
    initial_occupancy = parking_repository.get_occupancy_percentage(lot1.id)

    assert total_spots == 5
    assert initial_occupied == 2
    assert initial_vacant == 3

    available_node_id = None
    for node in all_nodes:
        if node.type == "PARKING_SPOT" and node.status == "AVAILABLE":
            available_node_id = node.id
            break

    assert available_node_id is not None
    updated_node = parking_repository.update_node_status(
        available_node_id, NodeStatus.OCCUPIED
    )
    assert updated_node.status == NodeStatus.OCCUPIED.value

    new_occupied = parking_repository.count_occupied_spots(lot1.id)
    new_vacant = parking_repository.count_vacant_spots(lot1.id)
    new_occupancy = parking_repository.get_occupancy_percentage(lot1.id)

    assert new_occupied == initial_occupied + 1
    assert new_vacant == initial_vacant - 1
    assert new_occupancy > initial_occupancy

    edges = parking_repository.edge_db.get_all_edges_for_lot(lot1.id)
    assert len(edges) == 2


def test_repository_error_handling(parking_repository):
    assert parking_repository.get_all_nodes_for_lot(999) == []
    assert parking_repository.get_all_edges_for_lot(999) == []
    assert parking_repository.count_spots(999) == 0
    assert parking_repository.count_occupied_spots(999) == 0
    assert parking_repository.count_vacant_spots(999) == 0
    assert parking_repository.get_occupancy_percentage(999) == 0.0

    assert parking_repository.get_node(999) is None
    assert parking_repository.update_node_status(999, NodeStatus.AVAILABLE) is None
