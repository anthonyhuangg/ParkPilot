import pytest
from database.models.parking import Base, NodeStatus, NodeType
from database.parking_database import EdgeDatabase, LotDatabase, NodeDatabase
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
def lot(db_session):
    """Creates a single parking lot"""
    lot_db = LotDatabase(db_session)
    return lot_db.create_lot({"name": "Lot A", "longitude": 151.2, "latitude": -33.9})


# lot db tests
def test_create_and_get_lot(db_session):
    lot_db = LotDatabase(db_session)
    created = lot_db.create_lot({"name": "TestLot", "longitude": 1.0, "latitude": 2.0})
    fetched = lot_db.get_lot_by_id(created.id)
    assert fetched.name == "TestLot"
    assert fetched.longitude == 1.0


def test_update_and_delete_lot(db_session):
    lot_db = LotDatabase(db_session)
    lot = lot_db.create_lot({"name": "Old", "longitude": 0.0, "latitude": 0.0})
    updated = lot_db.update_lot(lot.id, {"name": "New"})
    assert updated.name == "New"

    result = lot_db.delete_lot(lot.id)
    assert result is True
    assert lot_db.get_lot_by_id(lot.id) is None


def test_update_lot_invalid_id(db_session):
    assert LotDatabase(db_session).update_lot(999, {"name": "x"}) is None


def test_delete_lot_invalid_id(db_session):
    assert LotDatabase(db_session).delete_lot(999) is False


# node db test
def test_create_and_get_node(db_session, lot):
    node_db = NodeDatabase(db_session)
    node = node_db.create_node(
        {
            "lot_id": lot.id,
            "type": NodeType.PARKING_SPOT,
            "x": 1.0,
            "y": 2.0,
            "status": NodeStatus.AVAILABLE,
        }
    )
    fetched = node_db.get_node_by_id(node.id)
    assert fetched.id == node.id
    assert fetched.status == NodeStatus.AVAILABLE


def test_get_all_nodes_for_lot(db_session, lot):
    node_db = NodeDatabase(db_session)
    for i in range(3):
        node_db.create_node(
            {"lot_id": lot.id, "type": NodeType.ROAD, "x": i, "y": i + 1}
        )
    nodes = node_db.get_all_nodes_for_lot(lot.id)
    assert len(nodes) == 3


def test_update_node_status(db_session, lot):
    node_db = NodeDatabase(db_session)
    node = node_db.create_node(
        {
            "lot_id": lot.id,
            "type": NodeType.ROAD,
            "x": 0,
            "y": 0,
            "status": NodeStatus.OCCUPIED,
        }
    )
    updated = node_db.update_node_status(node.id, NodeStatus.AVAILABLE)
    assert updated.status == NodeStatus.AVAILABLE


def test_update_node_status_invalid_id(db_session):
    node_db = NodeDatabase(db_session)
    result = node_db.update_node_status(123, NodeStatus.AVAILABLE)
    assert result is None


def test_update_node_location(db_session, lot):
    node_db = NodeDatabase(db_session)
    node = node_db.create_node(
        {"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0}
    )
    updated = node_db.update_node_location(node.id, 9.9, 8.8)
    assert (updated.x, updated.y) == (9.9, 8.8)


def test_update_node_location_invalid_id(db_session):
    node_db = NodeDatabase(db_session)
    assert node_db.update_node_location(999, 1, 2) is None


def test_delete_node(db_session, lot):
    node_db = NodeDatabase(db_session)
    node = node_db.create_node(
        {"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0}
    )
    assert node_db.delete_node(node.id) is True
    assert node_db.get_node_by_id(node.id) is None


def test_delete_node_invalid_id(db_session):
    node_db = NodeDatabase(db_session)
    assert node_db.delete_node(999) is False


def test_counting_methods(db_session, lot):
    node_db = NodeDatabase(db_session)
    node_db.create_node(
        {
            "lot_id": lot.id,
            "type": NodeType.PARKING_SPOT,
            "x": 0,
            "y": 0,
            "status": NodeStatus.AVAILABLE,
        }
    )
    node_db.create_node(
        {
            "lot_id": lot.id,
            "type": NodeType.PARKING_SPOT,
            "x": 1,
            "y": 1,
            "status": NodeStatus.OCCUPIED,
        }
    )
    node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 2, "y": 2})

    assert node_db.count_spots(lot.id) == 2
    assert node_db.count_vacant_spots(lot.id) == 1
    assert node_db.count_nodes_by_type(lot.id, NodeType.ROAD) == 1


# edge db tests
def test_create_and_get_edge(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 2, "y": 2})

    edge_db = EdgeDatabase(db_session)
    edge = edge_db.create_edge(
        {
            "lot_id": lot.id,
            "from_node_id": n1.id,
            "to_node_id": n2.id,
            "length_m": 5.0,
            "weight": 1.0,
        }
    )
    fetched = edge_db.get_edge_by_id(edge.id)
    assert fetched.length_m == 5.0


def test_get_all_edges_for_lot(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    edge_db = EdgeDatabase(db_session)
    for _ in range(3):
        edge_db.create_edge(
            {
                "lot_id": lot.id,
                "from_node_id": n1.id,
                "to_node_id": n2.id,
                "length_m": 10.0,
                "weight": 5.0,
            }
        )
    edges = edge_db.get_all_edges_for_lot(lot.id)
    assert len(edges) == 3


def test_get_edges_between(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    edge_db = EdgeDatabase(db_session)
    edge_db.create_edge(
        {
            "lot_id": lot.id,
            "from_node_id": n1.id,
            "to_node_id": n2.id,
            "length_m": 2.0,
            "weight": 1.0,
        }
    )
    results = edge_db.get_edges_between(lot.id, n1.id, n2.id)
    assert len(results) == 1
    assert results[0].from_node_id == n1.id


def test_update_edge_status(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    edge_db = EdgeDatabase(db_session)
    edge = edge_db.create_edge(
        {
            "lot_id": lot.id,
            "from_node_id": n1.id,
            "to_node_id": n2.id,
            "length_m": 1.0,
            "weight": 1.0,
            "status": "OPEN",
        }
    )
    updated = edge_db.update_edge_status(edge.id, "CLOSED")
    assert updated.status == "CLOSED"


def test_update_edge_status_invalid(db_session):
    edge_db = EdgeDatabase(db_session)
    assert edge_db.update_edge_status(999, "OPEN") is None


def test_update_edge_weight_and_length(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    edge_db = EdgeDatabase(db_session)
    edge = edge_db.create_edge(
        {
            "lot_id": lot.id,
            "from_node_id": n1.id,
            "to_node_id": n2.id,
            "length_m": 1.0,
            "weight": 1.0,
        }
    )
    updated = edge_db.update_edge_weight(edge.id, weight=5.0, length_m=10.0)
    assert (updated.weight, updated.length_m) == (5.0, 10.0)


def test_update_edge_weight_invalid(db_session):
    edge_db = EdgeDatabase(db_session)
    assert edge_db.update_edge_weight(999, 5.0) is None


def test_delete_edge(db_session, lot):
    node_db = NodeDatabase(db_session)
    n1 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 0, "y": 0})
    n2 = node_db.create_node({"lot_id": lot.id, "type": NodeType.ROAD, "x": 1, "y": 1})
    edge_db = EdgeDatabase(db_session)
    edge = edge_db.create_edge(
        {
            "lot_id": lot.id,
            "from_node_id": n1.id,
            "to_node_id": n2.id,
            "length_m": 1.0,
            "weight": 1.0,
        }
    )
    assert edge_db.delete_edge(edge.id) is True
    assert edge_db.get_edge_by_id(edge.id) is None


def test_delete_edge_invalid(db_session):
    edge_db = EdgeDatabase(db_session)
    assert edge_db.delete_edge(999) is False
