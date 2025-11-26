import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app
from database.setup import create_tables


@pytest.fixture(scope="module")
def client():
    create_tables()
    return TestClient(app)


def get_recent_dates():
    """Helper to generate dates guaranteed to be in the last 30 days of seeded data."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    return {
        "today_str": today.isoformat(),
        "yesterday_str": yesterday.isoformat(),
        "seven_days_ago_str": seven_days_ago.isoformat(),
        "thirty_days_ago_str": thirty_days_ago.isoformat(),
    }


def test_hourly_occupancy(client):
    """
    Test the /api/parking/occupancy/hourly endpoint.
    Ensures hourly occupancy data is returned with correct structure.
    """
    dates = get_recent_dates()
    test_date = dates["yesterday_str"]
    lot_id = 1

    response = client.get(
        "/api/parking/occupancy/hourly",
        params={
            "date": test_date,
            "lot_id": lot_id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    # Check if the result is NOT empty
    assert len(data) > 0, (
        "Returned empty list - Check database/query implementation! "
        "Ensure OccupancyRepository.record_occupancy includes db.commit()"
    )

    # Verify structure
    assert "time" in data[0], "Missing 'time' key in hourly response"
    assert "used" in data[0], "Missing 'used' key in hourly response"


def test_daily_occupancy(client):
    """
    Test the /api/parking/occupancy/daily endpoint.
    Ensures daily occupancy data is returned for a date range.
    """
    dates = get_recent_dates()
    start_date = dates["seven_days_ago_str"]
    end_date = dates["today_str"]
    lot_id = 1

    response = client.get(
        "/api/parking/occupancy/daily",
        params={
            "start": start_date,
            "end": end_date,
            "lot_id": lot_id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    # Check if the result is NOT empty
    assert len(data) > 0, "Returned empty list - Check database/query implementation!"

    assert "date" in data[0], "Missing 'date' key in daily response"
    assert "used" in data[0], "Missing 'used' key in daily response"


def test_monthly_occupancy(client):
    """
    Test the /api/parking/occupancy/monthly endpoint.
    Ensures monthly occupancy data is returned for a date range.
    """
    dates = get_recent_dates()
    start_date = dates["thirty_days_ago_str"]
    end_date = dates["today_str"]
    lot_id = 1

    response = client.get(
        "/api/parking/occupancy/monthly",
        params={
            "start": start_date,
            "end": end_date,
            "lot_id": lot_id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    # Check if the result is NOT empty
    assert len(data) > 0, "Returned empty list - Check database/query implementation!"

    assert "month" in data[0], "Missing 'month' key in monthly response"
    assert "used" in data[0], "Missing 'used' key in monthly response"


def test_hourly_occupancy_different_lot(client):
    """Test hourly occupancy endpoint with a different lot ID."""
    dates = get_recent_dates()
    test_date = dates["yesterday_str"]
    lot_id = 2

    response = client.get(
        "/api/parking/occupancy/hourly",
        params={
            "date": test_date,
            "lot_id": lot_id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    # Verify structure (may be empty if no data for lot 2)
    if len(data) > 0:
        assert "time" in data[0]
        assert "used" in data[0]


def test_daily_occupancy_single_day(client):
    """Test daily occupancy with start and end on the same day."""
    dates = get_recent_dates()
    single_date = dates["yesterday_str"]
    lot_id = 1

    response = client.get(
        "/api/parking/occupancy/daily",
        params={
            "start": single_date,
            "end": single_date,
            "lot_id": lot_id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    # Should return at least one day of data
    if len(data) > 0:
        assert "date" in data[0]
        assert "used" in data[0]
