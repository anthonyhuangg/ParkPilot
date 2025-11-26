import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from application.services.carbon_saving_service import CarbonSavingService
from application.models.carbon_saving import (
    CarbonSavingCreate,
    UserTotalSavingsResponse,
    LotSavingsSummary,
    ContributorSavings,
)


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return CarbonSavingService(repository=mock_repo)


def test_calculate_and_record_saving(service, mock_repo):
    saving_data = CarbonSavingCreate(
        user_id=1,
        lot_id=10,
        distance_traveled_m=200,
    )

    baseline_distance = service.BASELINE_TIME_MIN * service.AVERAGE_SPEED_M_PER_MIN
    expected_distance_saved = max(0, baseline_distance - 200)

    expected_co2_g = expected_distance_saved * service.CO2_G_PER_M
    expected_money = (expected_co2_g / 1000) * service.MONEY_PER_KG_CO2_AUD

    mock_repo.add_saving.return_value = {"success": True}

    result = service.calculate_and_record_saving(saving_data)

    mock_repo.add_saving.assert_called_once_with(
        user_id=1,
        lot_id=10,
        distance_saved_m=pytest.approx(expected_distance_saved),
        co2_saved_g=pytest.approx(expected_co2_g),
        money_saved_usd=pytest.approx(expected_money),
    )

    assert result == {"success": True}


def test_calculate_and_record_saving_failure(service, mock_repo):
    saving_data = CarbonSavingCreate(user_id=1, lot_id=1, distance_traveled_m=100)

    mock_repo.add_saving.side_effect = Exception("DB error")

    with pytest.raises(HTTPException) as exc:
        service.calculate_and_record_saving(saving_data)

    assert exc.value.status_code == 500
    assert "Failed to record saving data" in exc.value.detail


def test_no_savings_when_traveled_more_than_baseline(service, mock_repo):
    saving_data = CarbonSavingCreate(
        user_id=1, lot_id=10, distance_traveled_m=2000  # larger than baseline
    )

    mock_repo.add_saving.return_value = {"success": True}

    result = service.calculate_and_record_saving(saving_data)

    mock_repo.add_saving.assert_called_once()
    args = mock_repo.add_saving.call_args.kwargs

    assert args["distance_saved_m"] == 0
    assert args["co2_saved_g"] == 0
    assert args["money_saved_usd"] == 0
    assert result == {"success": True}


def test_get_user_dashboard_valid(service, mock_repo):
    class FakeResult:
        total_co2_saved_g = 1200
        total_money_saved_usd = 3.5

    mock_repo.get_total_user_savings.return_value = FakeResult()

    response = service.get_user_dashboard(user_id=1)

    assert isinstance(response, UserTotalSavingsResponse)
    assert response.total_co2_saved_kg == 1.2
    assert response.total_money_saved_usd == 3.5


def test_get_user_dashboard_no_data(service, mock_repo):
    mock_repo.get_total_user_savings.return_value = None

    response = service.get_user_dashboard(user_id=1)

    assert response.total_co2_saved_kg == 0
    assert response.total_money_saved_usd == 0


def test_get_operator_dashboard(service, mock_repo):
    class Summary:
        total_co2_saved_g = 500
        total_money_saved_usd = 1.2

    mock_repo.get_lot_savings_summary_by_date.return_value = Summary()
    mock_repo.get_lot_contributors_by_date.return_value = [
        ContributorSavings(
            user_id=1,
            user_name="Alice",
            total_co2_saved_kg=0.5,
            total_money_saved_usd=0.2,
        )
    ]

    result = service.get_operator_dashboard(lot_id=10, date_str="2024-11-01")

    assert isinstance(result, LotSavingsSummary)
    assert result.total_co2_saved_kg == 0.5
    assert result.total_money_saved_usd == 1.2
    assert len(result.contributors) == 1
    assert result.contributors[0].user_name == "Alice"


def test_get_operator_dashboard_invalid_date(service):
    with pytest.raises(HTTPException) as e:
        service.get_operator_dashboard(lot_id=10, date_str="BAD_DATE")

    assert e.value.status_code == 400
    assert "Invalid date format" in e.value.detail
