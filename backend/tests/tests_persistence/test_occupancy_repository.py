import pytest
from datetime import datetime, timedelta
from persistence.occupancy_repository import OccupancyRepository
from database.models.occupancy import Base
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
def occupancy_repository(db_session):
    return OccupancyRepository(db_session)


@pytest.fixture
def sample_occupancy_data(db_session, occupancy_repository):
    """Creates sample occupancy data spanning multiple time periods."""
    base_date = datetime(2024, 1, 15, 0, 0, 0)

    # Create hourly data for a single day (Jan 15)
    events = []
    for hour in range(24):
        for _ in range(hour + 1):  # Hour 0 has 1 event, hour 1 has 2, etc.
            ts = base_date + timedelta(hours=hour, minutes=15)
            event = occupancy_repository.record_occupancy(
                lot_id=1, node_id=101, timestamp=ts
            )
            events.append(event)

    # Create daily data for a week (Jan 15-21)
    for day in range(7):
        for _ in range((day + 1) * 10):  # Day 0 has 10 events, day 1 has 20, etc.
            ts = base_date + timedelta(days=day, hours=12)
            event = occupancy_repository.record_occupancy(
                lot_id=1, node_id=102, timestamp=ts
            )
            events.append(event)

    # Create data for a second lot
    for hour in range(5):
        for _ in range(5):
            ts = base_date + timedelta(hours=hour)
            event = occupancy_repository.record_occupancy(
                lot_id=2, node_id=201, timestamp=ts
            )
            events.append(event)

    # Create monthly data (Jan, Feb, Mar)
    jan_date = datetime(2024, 1, 10, 12, 0, 0)
    feb_date = datetime(2024, 2, 10, 12, 0, 0)
    mar_date = datetime(2024, 3, 10, 12, 0, 0)

    for _ in range(100):
        occupancy_repository.record_occupancy(lot_id=1, node_id=103, timestamp=jan_date)
    for _ in range(150):
        occupancy_repository.record_occupancy(lot_id=1, node_id=103, timestamp=feb_date)
    for _ in range(200):
        occupancy_repository.record_occupancy(lot_id=1, node_id=103, timestamp=mar_date)

    return events


def test_record_occupancy_with_timestamp(occupancy_repository):
    """Test recording an occupancy event with a specific timestamp."""
    ts = datetime(2024, 1, 1, 10, 30, 0)
    occ = occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=ts)

    assert occ.id is not None
    assert occ.lot_id == 1
    assert occ.node_id == 100
    assert occ.timestamp == ts


def test_record_occupancy_without_timestamp(occupancy_repository):
    """Test recording an occupancy event with default timestamp."""
    before = datetime.utcnow()
    occ = occupancy_repository.record_occupancy(lot_id=2, node_id=200)
    after = datetime.utcnow()

    assert occ.id is not None
    assert occ.lot_id == 2
    assert occ.node_id == 200
    assert before <= occ.timestamp <= after


def test_record_occupancy_multiple_events(occupancy_repository):
    """Test recording multiple occupancy events."""
    ts1 = datetime(2024, 1, 1, 10, 0, 0)
    ts2 = datetime(2024, 1, 1, 11, 0, 0)
    ts3 = datetime(2024, 1, 1, 12, 0, 0)

    occ1 = occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=ts1)
    occ2 = occupancy_repository.record_occupancy(lot_id=1, node_id=101, timestamp=ts2)
    occ3 = occupancy_repository.record_occupancy(lot_id=2, node_id=200, timestamp=ts3)

    assert occ1.id != occ2.id != occ3.id
    assert occ1.lot_id == 1
    assert occ2.lot_id == 1
    assert occ3.lot_id == 2


def test_count_between_basic(occupancy_repository):
    """Test counting events between two timestamps."""
    base = datetime(2024, 1, 1, 10, 0, 0)

    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=base)
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(minutes=30)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(hours=1)
    )

    start = base
    end = base + timedelta(hours=1)
    count = occupancy_repository._count_between(start, end)

    assert count == 2  # First two events, third is at end boundary (exclusive)


def test_count_between_inclusive_start_exclusive_end(occupancy_repository):
    """Test that start is inclusive and end is exclusive."""
    start = datetime(2024, 1, 1, 10, 0, 0)
    end = datetime(2024, 1, 1, 11, 0, 0)

    # Event exactly at start (should be included)
    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=start)
    # Event exactly at end (should be excluded)
    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=end)

    count = occupancy_repository._count_between(start, end)
    assert count == 1


def test_count_between_with_lot_filter(occupancy_repository):
    """Test counting events filtered by lot_id."""
    base = datetime(2024, 1, 1, 10, 0, 0)

    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=1, node_id=101, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=2, node_id=200, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=2, node_id=201, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=2, node_id=202, timestamp=base)

    start = base - timedelta(hours=1)
    end = base + timedelta(hours=1)

    count_lot1 = occupancy_repository._count_between(start, end, lot_id=1)
    count_lot2 = occupancy_repository._count_between(start, end, lot_id=2)
    count_all = occupancy_repository._count_between(start, end)

    assert count_lot1 == 2
    assert count_lot2 == 3
    assert count_all == 5


def test_count_between_empty_range(occupancy_repository):
    """Test counting when no events exist in range."""
    base = datetime(2024, 1, 1, 10, 0, 0)
    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=base)

    start = base + timedelta(hours=5)
    end = base + timedelta(hours=10)
    count = occupancy_repository._count_between(start, end)

    assert count == 0


def test_count_between_no_events(occupancy_repository):
    """Test counting when database is empty."""
    start = datetime(2024, 1, 1, 10, 0, 0)
    end = datetime(2024, 1, 1, 11, 0, 0)
    count = occupancy_repository._count_between(start, end)

    assert count == 0


def test_get_hourly_for_date_basic(occupancy_repository):
    """Test getting hourly data for a specific date."""
    date_str = "2024-01-15"
    base = datetime(2024, 1, 15, 0, 0, 0)

    # Add events at different hours
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(hours=8)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(hours=8, minutes=30)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(hours=14)
    )

    result = occupancy_repository.get_hourly_for_date(date_str)

    assert len(result) == 24
    assert result[0] == {"time": "00:00", "used": 0}
    assert result[8] == {"time": "08:00", "used": 2}
    assert result[14] == {"time": "14:00", "used": 1}
    assert result[23] == {"time": "23:00", "used": 0}


def test_get_hourly_for_date_with_lot_filter(occupancy_repository):
    """Test getting hourly data filtered by lot_id."""
    date_str = "2024-01-15"
    base = datetime(2024, 1, 15, 10, 0, 0)

    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=1, node_id=101, timestamp=base)
    occupancy_repository.record_occupancy(lot_id=2, node_id=200, timestamp=base)

    result_lot1 = occupancy_repository.get_hourly_for_date(date_str, lot_id=1)
    result_lot2 = occupancy_repository.get_hourly_for_date(date_str, lot_id=2)

    assert result_lot1[10] == {"time": "10:00", "used": 2}
    assert result_lot2[10] == {"time": "10:00", "used": 1}


def test_get_hourly_for_date_no_data(occupancy_repository):
    """Test getting hourly data when no events exist."""
    date_str = "2024-01-15"
    result = occupancy_repository.get_hourly_for_date(date_str)

    assert len(result) == 24
    for hour_data in result:
        assert hour_data["used"] == 0


def test_get_hourly_for_date_boundary_times(occupancy_repository):
    """Test that events at hour boundaries are counted correctly."""
    date_str = "2024-01-15"
    base = datetime(2024, 1, 15, 0, 0, 0)

    # Event at exact hour boundary (should be included)
    occupancy_repository.record_occupancy(lot_id=1, node_id=100, timestamp=base)
    # Event at next hour boundary (should be in next hour)
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=base + timedelta(hours=1)
    )

    result = occupancy_repository.get_hourly_for_date(date_str)

    assert result[0] == {"time": "00:00", "used": 1}
    assert result[1] == {"time": "01:00", "used": 1}


def test_get_daily_range_basic(occupancy_repository):
    """Test getting daily counts for a date range."""
    start_date = "2024-01-15"
    end_date = "2024-01-17"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 14, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 16, 10, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 17, 15, 0, 0)
    )

    result = occupancy_repository.get_daily_range(start_date, end_date)

    assert len(result) == 3
    assert result[0] == {"date": "2024-01-15", "used": 2}
    assert result[1] == {"date": "2024-01-16", "used": 1}
    assert result[2] == {"date": "2024-01-17", "used": 1}


def test_get_daily_range_single_day(occupancy_repository):
    """Test getting daily counts for a single day."""
    start_date = "2024-01-15"
    end_date = "2024-01-15"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 10, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 14, 0, 0)
    )

    result = occupancy_repository.get_daily_range(start_date, end_date)

    assert len(result) == 1
    assert result[0] == {"date": "2024-01-15", "used": 2}


def test_get_daily_range_with_lot_filter(occupancy_repository):
    """Test getting daily counts filtered by lot_id."""
    start_date = "2024-01-15"
    end_date = "2024-01-15"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 10, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=2, node_id=200, timestamp=datetime(2024, 1, 15, 10, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=2, node_id=201, timestamp=datetime(2024, 1, 15, 11, 0, 0)
    )

    result_lot1 = occupancy_repository.get_daily_range(start_date, end_date, lot_id=1)
    result_lot2 = occupancy_repository.get_daily_range(start_date, end_date, lot_id=2)

    assert result_lot1[0] == {"date": "2024-01-15", "used": 1}
    assert result_lot2[0] == {"date": "2024-01-15", "used": 2}


def test_get_daily_range_invalid_range(occupancy_repository):
    """Test getting daily counts when end date is before start date."""
    start_date = "2024-01-20"
    end_date = "2024-01-15"

    result = occupancy_repository.get_daily_range(start_date, end_date)

    assert result == []


def test_get_daily_range_no_data(occupancy_repository):
    """Test getting daily counts when no events exist."""
    start_date = "2024-01-15"
    end_date = "2024-01-17"

    result = occupancy_repository.get_daily_range(start_date, end_date)

    assert len(result) == 3
    assert result[0] == {"date": "2024-01-15", "used": 0}
    assert result[1] == {"date": "2024-01-16", "used": 0}
    assert result[2] == {"date": "2024-01-17", "used": 0}


def test_get_daily_range_boundary_times(occupancy_repository):
    """Test that events at day boundaries are counted correctly."""
    start_date = "2024-01-15"
    end_date = "2024-01-16"

    # Event at exact day start (should be included in that day)
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 0, 0, 0)
    )
    # Event at next day start (should be in next day)
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 16, 0, 0, 0)
    )

    result = occupancy_repository.get_daily_range(start_date, end_date)

    assert result[0] == {"date": "2024-01-15", "used": 1}
    assert result[1] == {"date": "2024-01-16", "used": 1}


def test_get_monthly_range_basic(occupancy_repository):
    """Test getting monthly counts for a date range."""
    start_date = "2024-01-01"
    end_date = "2024-03-31"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 20, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 2, 10, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 3, 5, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 3, 25, 12, 0, 0)
    )

    result = occupancy_repository.get_monthly_range(start_date, end_date)

    assert len(result) == 3
    assert result[0] == {"month": "2024-01", "used": 2}
    assert result[1] == {"month": "2024-02", "used": 1}
    assert result[2] == {"month": "2024-03", "used": 2}


def test_get_monthly_range_single_month(occupancy_repository):
    """Test getting monthly counts for a single month."""
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 20, 12, 0, 0)
    )

    result = occupancy_repository.get_monthly_range(start_date, end_date)

    assert len(result) == 1
    assert result[0] == {"month": "2024-01", "used": 2}


def test_get_monthly_range_with_lot_filter(occupancy_repository):
    """Test getting monthly counts filtered by lot_id."""
    start_date = "2024-01-01"
    end_date = "2024-02-29"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=2, node_id=200, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=2, node_id=201, timestamp=datetime(2024, 1, 20, 12, 0, 0)
    )

    result_lot1 = occupancy_repository.get_monthly_range(start_date, end_date, lot_id=1)
    result_lot2 = occupancy_repository.get_monthly_range(start_date, end_date, lot_id=2)

    assert result_lot1[0] == {"month": "2024-01", "used": 1}
    assert result_lot2[0] == {"month": "2024-01", "used": 2}


def test_get_monthly_range_year_boundary(occupancy_repository):
    """Test getting monthly counts across year boundary."""
    start_date = "2023-11-01"
    end_date = "2024-02-29"

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2023, 11, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2023, 12, 25, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 10, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 2, 5, 12, 0, 0)
    )

    result = occupancy_repository.get_monthly_range(start_date, end_date)

    assert len(result) == 4
    assert result[0] == {"month": "2023-11", "used": 1}
    assert result[1] == {"month": "2023-12", "used": 1}
    assert result[2] == {"month": "2024-01", "used": 1}
    assert result[3] == {"month": "2024-02", "used": 1}


def test_get_monthly_range_no_data(occupancy_repository):
    """Test getting monthly counts when no events exist."""
    start_date = "2024-01-01"
    end_date = "2024-03-31"

    result = occupancy_repository.get_monthly_range(start_date, end_date)

    assert len(result) == 3
    assert result[0] == {"month": "2024-01", "used": 0}
    assert result[1] == {"month": "2024-02", "used": 0}
    assert result[2] == {"month": "2024-03", "used": 0}


def test_get_monthly_range_partial_month_dates(occupancy_repository):
    """Test that partial month dates are handled correctly."""
    start_date = "2024-01-15"  # Mid-month
    end_date = "2024-03-20"  # Mid-month

    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 1, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 25, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 2, 15, 12, 0, 0)
    )
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 3, 15, 12, 0, 0)
    )

    result = occupancy_repository.get_monthly_range(start_date, end_date)

    # Should include full months from Jan to Mar
    assert len(result) == 3
    assert result[0] == {"month": "2024-01", "used": 2}
    assert result[1] == {"month": "2024-02", "used": 1}
    assert result[2] == {"month": "2024-03", "used": 1}


def test_repository_workflow_integration(occupancy_repository, sample_occupancy_data):
    """Test complete workflow with realistic data."""
    # Test hourly data retrieval
    hourly_data = occupancy_repository.get_hourly_for_date("2024-01-15", lot_id=1)
    assert len(hourly_data) == 24
    assert sum(hour["used"] for hour in hourly_data) > 0

    # Test daily data retrieval
    daily_data = occupancy_repository.get_daily_range(
        "2024-01-15", "2024-01-21", lot_id=1
    )
    assert len(daily_data) == 7
    assert all(day["used"] > 0 for day in daily_data)

    # Test monthly data retrieval
    monthly_data = occupancy_repository.get_monthly_range(
        "2024-01-01", "2024-03-31", lot_id=1
    )
    assert len(monthly_data) == 3
    assert monthly_data[0]["month"] == "2024-01"
    assert monthly_data[1]["month"] == "2024-02"
    assert monthly_data[2]["month"] == "2024-03"

    # Test lot filtering
    lot2_data = occupancy_repository.get_hourly_for_date("2024-01-15", lot_id=2)
    assert sum(hour["used"] for hour in lot2_data) > 0


def test_repository_error_handling(occupancy_repository):
    """Test repository handles edge cases gracefully."""
    # Empty database queries
    assert occupancy_repository.get_hourly_for_date("2024-01-15") == [
        {"time": f"{h:02d}:00", "used": 0} for h in range(24)
    ]

    assert occupancy_repository.get_daily_range("2024-01-15", "2024-01-17") == [
        {"date": "2024-01-15", "used": 0},
        {"date": "2024-01-16", "used": 0},
        {"date": "2024-01-17", "used": 0},
    ]

    assert occupancy_repository.get_monthly_range("2024-01-01", "2024-03-31") == [
        {"month": "2024-01", "used": 0},
        {"month": "2024-02", "used": 0},
        {"month": "2024-03", "used": 0},
    ]

    # Invalid date range
    assert occupancy_repository.get_daily_range("2024-01-20", "2024-01-15") == []

    # Non-existent lot
    occupancy_repository.record_occupancy(
        lot_id=1, node_id=100, timestamp=datetime(2024, 1, 15, 12, 0, 0)
    )
    result = occupancy_repository.get_hourly_for_date("2024-01-15", lot_id=999)
    assert all(hour["used"] == 0 for hour in result)
