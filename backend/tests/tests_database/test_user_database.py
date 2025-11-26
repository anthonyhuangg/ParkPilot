import pytest
from database.models.user import Base, UserDatabaseModel
from database.user_database import UserDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    engine.dispose()


@pytest.fixture
def user_db(session):
    return UserDatabase(session)


@pytest.fixture
def sample_user(user_db):
    user = user_db.create_user(
        name="Alice",
        email="alice@example.com",
        password_hash="hashedpw",
        role="driver",
        car_reg="ABC123",
    )
    return user


def test_create_user(user_db, session):
    user = user_db.create_user(
        name="Bob",
        email="bob@example.com",
        password_hash="hashedpw",
        role="admin",
        car_reg="XYZ789",
    )
    assert user.id is not None
    assert user.email == "bob@example.com"

    # Verify persisted in DB
    fetched = (
        session.query(UserDatabaseModel).filter_by(email="bob@example.com").first()
    )
    assert fetched.name == "Bob"
    assert fetched.role == "admin"


def test_get_all_users(user_db):
    user_db.create_user("A", "a@x.com", "p", "driver", "C1")
    user_db.create_user("B", "b@x.com", "p", "driver", "C2")

    all_users = user_db.get_all_users()
    assert len(all_users) == 2
    assert {u.email for u in all_users} == {"a@x.com", "b@x.com"}


def test_get_user_by_id(user_db, sample_user):
    user = user_db.get_user_by_id(sample_user.id)
    assert user is not None
    assert user.email == "alice@example.com"

    missing = user_db.get_user_by_id(999)
    assert missing is None


def test_get_user_by_email_full(user_db, sample_user):
    user = user_db.get_user_by_email("alice@example.com", include_password=True)
    assert hasattr(user, "password_hash")
    assert user.password_hash == "hashedpw"


def test_get_user_by_email_without_password(user_db, sample_user):
    result = user_db.get_user_by_email("alice@example.com", include_password=False)
    cols = result._fields
    assert "id" in cols or "id" in cols
    assert "password_hash" not in cols
    assert "email" in cols


def test_get_user_by_email_not_found(user_db):
    assert user_db.get_user_by_email("notfound@example.com") is None
