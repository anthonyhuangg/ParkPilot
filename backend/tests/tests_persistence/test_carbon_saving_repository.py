import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.carbon_saving_repository import CarbonSavingRepository
from database.models.carbon_saving import CarbonSaving
from database.models.user import UserDatabaseModel
from database.setup import Base


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def repository(test_db):
    """Returns a CarbonSavingRepository using the in-memory DB."""
    return CarbonSavingRepository(test_db)


def test_add_saving(repository, test_db):
    new_saving = repository.add_saving(
        user_id=1,
        lot_id=3,
        distance_saved_m=100,
        co2_saved_g=50,
        money_saved_usd=0.5,
    )

    assert new_saving.id is not None
    assert new_saving.user_id == 1
    assert new_saving.co2_saved_g == 50

    saved = test_db.query(CarbonSaving).filter_by(id=new_saving.id).first()
    assert saved is not None


def test_get_total_user_savings(repository, test_db):
    test_db.add_all(
        [
            CarbonSaving(
                user_id=1,
                lot_id=3,
                route_length_saved_m=100,
                co2_saved_g=50,
                money_saved_usd=0.5,
            ),
            CarbonSaving(
                user_id=1,
                lot_id=4,
                route_length_saved_m=50,
                co2_saved_g=30,
                money_saved_usd=0.3,
            ),
        ]
    )
    test_db.commit()

    result = repository.get_total_user_savings(1)

    assert result.total_co2_saved_g == 80
    assert result.total_money_saved_usd == 0.8


def test_get_lot_savings_summary_by_date(repository, test_db):
    today = datetime(2024, 11, 15)

    saving1 = CarbonSaving(
        user_id=1,
        lot_id=2,
        route_length_saved_m=150,
        co2_saved_g=75,
        money_saved_usd=1.0,
        date_time=today,
    )

    saving2 = CarbonSaving(
        user_id=2,
        lot_id=2,
        route_length_saved_m=50,
        co2_saved_g=25,
        money_saved_usd=0.2,
        date_time=today,
    )

    test_db.add_all([saving1, saving2])
    test_db.commit()

    summary = repository.get_lot_savings_summary_by_date(2, "2024-11-15")
    assert summary.total_co2_saved_g == 100
    assert summary.total_money_saved_usd == 1.2


def test_get_lot_contributors_by_date(repository, test_db):
    u1 = UserDatabaseModel(
        id=1,
        name="Alice",
        email="alice@test.com",
        password_hash="hash",
        role="user",
        car_reg="ABC123",
    )

    u2 = UserDatabaseModel(
        id=2,
        name="Bob",
        email="bob@test.com",
        password_hash="hash2",
        role="user",
        car_reg="XYZ789",
    )

    day = datetime(2024, 11, 15)

    s1 = CarbonSaving(
        user_id=1,
        lot_id=5,
        route_length_saved_m=100,
        co2_saved_g=90,
        money_saved_usd=1.0,
        date_time=day,
    )

    s2 = CarbonSaving(
        user_id=2,
        lot_id=5,
        route_length_saved_m=50,
        co2_saved_g=40,
        money_saved_usd=0.5,
        date_time=day,
    )

    s3 = CarbonSaving(
        user_id=1,
        lot_id=5,
        route_length_saved_m=30,
        co2_saved_g=10,
        money_saved_usd=0.2,
        date_time=day,
    )

    test_db.add_all([u1, u2, s1, s2, s3])
    test_db.commit()

    contributors = repository.get_lot_contributors_by_date(5, "2024-11-15")

    assert len(contributors) == 2
    assert contributors[0].user_id == 1
    assert contributors[1].user_id == 2

    assert contributors[0].total_co2_saved_kg == 0.1
    assert contributors[1].total_co2_saved_kg == 0.04

    assert contributors[0].user_name == "Alice"
    assert contributors[1].user_name == "Bob"
