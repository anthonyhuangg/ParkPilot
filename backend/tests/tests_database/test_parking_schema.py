import pytest
from database.models.parking import Base
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="module")
def inspector():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return inspect(engine)


def test__tables_exist(inspector):
    tables = inspector.get_table_names()
    expected = {"parking_lots", "graph_nodes", "graph_edges"}
    missing = expected - set(tables)
    assert not missing, f"Missing tables: {missing}"


def test_graph_nodes_columns(inspector):
    columns = {col["name"]: col for col in inspector.get_columns("graph_nodes")}
    expected_columns = {
        "id",
        "lot_id",
        "type",
        "x",
        "y",
        "orientation",
        "status",
        "label",
        "sensor_id",
        "attrs",
        "expires_at",
    }
    assert expected_columns.issubset(columns.keys())

    # Check columns
    assert not columns["lot_id"]["nullable"]
    assert not columns["type"]["nullable"]
    assert "INTEGER" in str(columns["id"]["type"]).upper()
    assert "FLOAT" in str(columns["x"]["type"]).upper()
    assert "FLOAT" in str(columns["y"]["type"]).upper()


def test_foreign_keys_graph_nodes(inspector):
    fks = inspector.get_foreign_keys("graph_nodes")
    fk_cols = {fk["constrained_columns"][0]: fk["referred_table"] for fk in fks}
    assert fk_cols.get("lot_id") == "parking_lots"


def test_foreign_keys_graph_edges(inspector):
    fks = inspector.get_foreign_keys("graph_edges")
    fk_map = {fk["constrained_columns"][0]: fk["referred_table"] for fk in fks}

    expected_fks = {
        "lot_id": "parking_lots",
        "from_node_id": "graph_nodes",
        "to_node_id": "graph_nodes",
    }
    for col, ref in expected_fks.items():
        assert fk_map.get(col) == ref, f"Missing FK for {col} → {ref}"


def test_primary_keys(inspector):
    pk_nodes = inspector.get_pk_constraint("graph_nodes")
    pk_edges = inspector.get_pk_constraint("graph_edges")
    pk_lots = inspector.get_pk_constraint("parking_lots")

    assert pk_nodes["constrained_columns"] == ["id"]
    assert pk_edges["constrained_columns"] == ["id"]
    assert pk_lots["constrained_columns"] == ["id"]


def test_enum_columns_types(inspector):
    columns = {col["name"]: col for col in inspector.get_columns("graph_nodes")}
    type_str = str(columns["type"]["type"]).lower()
    assert (
        "enum" in type_str or "varchar" in type_str
    ), "NodeType should be stored as Enum or String"


def test_graph_edges_references_existing_tables(inspector):
    fks = inspector.get_foreign_keys("graph_edges")
    referred_tables = {fk["referred_table"] for fk in fks}
    assert {"graph_nodes", "parking_lots"}.issubset(referred_tables)
