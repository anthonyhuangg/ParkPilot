import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from application.models.user import UserCreate, UserResponse
from jose import jwt
from passlib.context import CryptContext
from persistence.user_repository import UserRepository
from database.models.user import UserDatabaseModel

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set in environment variables!")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180


class UserService:
    """Handles all user-related operations and authentication logic."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user: UserCreate) -> UserResponse:
        """
        Register a new user with validation and password hashing.

        Args:
            user: Pydantic model containing user registration data.

        Returns:
            UserResponse: The created user (without password).

        Raises:
            ValueError: If validation fails or email already exists.
        """
        if not user.name or not user.name.strip():
            raise ValueError("User name cannot be empty.")

        if not user.email or not user.email.strip():
            raise ValueError("User email cannot be empty.")

        existing_user = self.user_repository.get_user_by_email(
            user.email, include_password=False
        )
        if existing_user:
            raise ValueError(f"User with email '{user.email}' already exists.")

        allowed_roles = {"dr", "po"}
        if user.role not in allowed_roles:
            raise ValueError(
                f"Invalid role specified: '{user.role}'. "
                f"Role must be one of {list(allowed_roles)}."
            )

        hashed_password = pwd_context.hash(user.password[:72])

        return self.user_repository.create_user(
            name=user.name,
            email=user.email,
            password_hash=hashed_password,
            role=user.role,
            car_reg=user.car_reg,
        )

    def get_all_users(self) -> List[UserResponse]:
        """Retrieve all users"""
        return self.user_repository.get_all_users()

    def get_user_by_id(self, user_id: int) -> UserResponse:
        """Fetch a single user by ID."""
        if user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        db_user = self.user_repository.get_db_user_by_email(email)
        if not db_user:
            return None
        if not pwd_context.verify(password, db_user.password_hash):
            return None
        return UserResponse.model_validate(db_user)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        """
        Generate a JWT access token.

        Args:
            data: Dictionary of claims (e.g. {"sub": user.id, "role": user.role})
            expires_delta: Optional custom expiration

        Returns:
            str: Signed JWT token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID. Returns True if user existed and was deleted."""
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return False
        self.user_repository.delete_user(user_id)
        return True

    def update_user(self, user_id: int, user_update):
        """
        Update user fields (name, email, role, car_reg). Password not updated here.

        Args:
            user_id: ID of user to update
            user_update: Pydantic model with optional fields to update

        Returns:
            Updated UserResponse

        Raises:
            ValueError: If user not found
        """
        # Fetch the actual DB object (not Pydantic)
        existing_user = (
            self.user_repository.db.query(UserDatabaseModel)
            .filter_by(id=user_id)
            .first()
        )
        if not existing_user:
            raise ValueError("User not found")

        # Update only provided fields
        if user_update.name is not None:
            existing_user.name = user_update.name
        if user_update.email is not None:
            existing_user.email = user_update.email
        if user_update.role is not None:
            existing_user.role = user_update.role
        if user_update.car_reg is not None:
            existing_user.car_reg = user_update.car_reg

        self.user_repository.save(existing_user)

        return UserResponse.model_validate(existing_user, from_attributes=True)
