import pytest
from database.setup import Base
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="function")
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


def test_table_exists(engine):
    insp = inspect(engine)
    assert "users" in insp.get_table_names()


def test_columns_and_constraints(engine):
    insp = inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("users")}
    expected = {"id", "name", "email", "password_hash", "role", "car_reg", "created_at"}
    assert expected.issubset(cols.keys())

    pk = insp.get_pk_constraint("users")
    assert pk["constrained_columns"] == ["id"]

    for field in ["name", "email", "password_hash", "role", "car_reg"]:
        assert not cols[field]["nullable"]

    # types
    assert "INTEGER" in str(cols["id"]["type"]).upper()
    assert "VARCHAR" in str(cols["email"]["type"]).upper()
    assert "DATETIME" in str(cols["created_at"]["type"]).upper()
