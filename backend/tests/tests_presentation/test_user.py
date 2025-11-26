import pytest
from fastapi.testclient import TestClient
from main import app
from database.setup import create_tables
from database import SessionLocal
from database.models import user as user_model


@pytest.fixture(autouse=True)
def reset_db():
    """Reset the database before each test."""
    db = SessionLocal()
    user_model.Base.metadata.drop_all(bind=db.bind)
    user_model.Base.metadata.create_all(bind=db.bind)
    db.close()


@pytest.fixture(scope="module")
def client():
    """Creates a test client and ensures DB tables exist."""
    create_tables()
    return TestClient(app)


def sample_user_json():
    """Helper to create a consistent user payload."""
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "mypassword",
        "role": "dr",
        "car_reg": "XYZ123",
    }


def test_register_user(client):
    """Ensure user registration works and returns token + correct fields."""
    user_data = sample_user_json()
    response = client.post("/api/users/register", json=user_data)
    assert response.status_code == 200, response.text

    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"


def test_register_duplicate_email(client):
    """Should fail when registering the same email twice."""
    user_data = sample_user_json()
    client.post("/api/users/register", json=user_data)
    response = client.post("/api/users/register", json=user_data)

    # Should fail with 400 after duplicate check
    assert response.status_code in (400, 409), response.text


def test_login_valid(client):
    """Should log in with correct credentials."""
    user_data = sample_user_json()
    client.post("/api/users/register", json=user_data)

    response = client.post(
        "/api/users/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == user_data["email"]


def test_login_invalid_password(client):
    """Login fails with wrong password."""
    user_data = sample_user_json()
    client.post("/api/users/register", json=user_data)

    response = client.post(
        "/api/users/login",
        data={"username": user_data["email"], "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_all_users(client):
    """Retrieve list of users after registering two."""
    u1 = sample_user_json()
    u2 = {**sample_user_json(), "email": "second@example.com"}

    client.post("/api/users/register", json=u1)
    client.post("/api/users/register", json=u2)

    response = client.get("/api/users")
    assert response.status_code == 200

    users = response.json()
    assert len(users) >= 2
    emails = [u["email"] for u in users]
    assert "alice@example.com" in emails
    assert "second@example.com" in emails


def test_get_user_by_id(client):
    """Fetch user by ID returns correct record."""
    user_data = sample_user_json()
    res = client.post("/api/users/register", json=user_data)
    user_id = res.json()["user"]["id"]

    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["email"] == user_data["email"]
    assert "created_at" in data


def test_delete_user(client):
    """Delete existing user then verify 404 on repeat."""
    res = client.post("/api/users/register", json=sample_user_json())
    user_id = res.json()["user"]["id"]

    # Delete once
    del_res = client.delete(f"/api/users/{user_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "User deleted"

    # Delete again should 404
    del_res = client.delete(f"/api/users/{user_id}")
    assert del_res.status_code == 404


def test_update_user(client):
    """Test updating user information without password."""

    res = client.post("/api/users/register", json=sample_user_json())
    assert res.status_code == 200
    user_data = res.json()["user"]
    user_id = user_data["id"]

    update_payload = {
        "name": "Updated Name",
        "role": "dr",
        "car_reg": "XYZ999",
    }

    res = client.put(f"/api/users/{user_id}", json=update_payload)
    assert res.status_code == 200
    updated_user = res.json()

    assert updated_user["name"] == "Updated Name"
    assert updated_user["car_reg"] == "XYZ999"
    assert updated_user["role"] == "dr"
