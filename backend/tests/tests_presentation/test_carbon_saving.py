import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
import presentation.routes.carbon_saving as carbon_router


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[carbon_router.get_carbon_saving_service] = (
        lambda: mock_service
    )

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides = {}


# POST /carbon/record-saving
def test_record_saving_success(client, mock_service):
    mock_service.calculate_and_record_saving.return_value = None

    payload = {"user_id": 1, "lot_id": 10, "distance_traveled_m": 250}

    response = client.post("/carbon/record-saving", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Carbon saving recorded successfully."}
    mock_service.calculate_and_record_saving.assert_called_once()


def test_record_saving_failure(client, mock_service):
    mock_service.calculate_and_record_saving.side_effect = Exception("boom!")

    payload = {"user_id": 1, "lot_id": 10, "distance_traveled_m": 250}

    response = client.post("/carbon/record-saving", json=payload)

    # Depending on how your router wraps exceptions
    assert response.status_code in {400, 500}


# GET /carbon/user/{user_id}
def test_get_user_savings_success(client, mock_service):
    mock_service.get_user_dashboard.return_value = {
        "user_id": 1,
        "total_co2_saved_kg": 0.5,
        "total_money_saved_usd": 2.0,
    }

    response = client.get("/carbon/user/1")

    assert response.status_code == 200
    assert response.json()["total_co2_saved_kg"] == 0.5
    assert response.json()["total_money_saved_usd"] == 2.0


def test_get_user_savings_failure(client, mock_service):
    mock_service.get_user_dashboard.side_effect = Exception("oops")

    response = client.get("/carbon/user/1")

    assert response.status_code == 400
    assert "Failed to fetch user savings" in response.json()["detail"]


# GET /carbon/operator/lot/{lot_id}
def test_operator_dashboard_success(client, mock_service):
    mock_service.get_operator_dashboard.return_value = {
        "lot_id": 5,
        "date": "2024-11-15",
        "total_co2_saved_kg": 1.25,
        "total_money_saved_usd": 3.00,
        "contributors": [
            {
                "user_id": 1,
                "user_name": "Alice",
                "total_co2_saved_kg": 0.75,
                "total_money_saved_usd": 1.5,
            }
        ],
    }

    response = client.get("/carbon/operator/lot/5?date=2024-11-15")

    assert response.status_code == 200
    assert response.json()["total_co2_saved_kg"] == 1.25
    assert len(response.json()["contributors"]) == 1
    assert response.json()["contributors"][0]["user_name"] == "Alice"


def test_operator_dashboard_invalid_date(client, mock_service):
    from fastapi import HTTPException

    mock_service.get_operator_dashboard.side_effect = HTTPException(
        status_code=400, detail="Invalid date"
    )

    response = client.get("/carbon/operator/lot/5?date=BAD_DATE")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date"
