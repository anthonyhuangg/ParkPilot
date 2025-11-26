from datetime import timedelta
from typing import List

from application.models.user import UserCreate, UserResponse
from application.models.user_with_token import UserWithToken
from application.services.user_service import UserService
from database.setup import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from persistence.user_repository import UserRepository
from sqlalchemy.orm import Session
from application.models.user import UserUpdate

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 180


@router.post("/users/register", response_model=UserWithToken)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user: UserCreate model with user details.
        db: Database session.

    Returns:
        UserWithToken: The created user and their JWT token.

    Raises:
        HTTPException: If the email is already registered or invalid data is provided.
    """
    user_repository = UserRepository(db)
    service = UserService(user_repository)

    try:
        new_user = service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    access_token = service.create_access_token(data={"sub": new_user.email})
    return UserWithToken(user=new_user, access_token=access_token, token_type="bearer")


@router.post("/users/login", response_model=UserWithToken)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate user and provide JWT token.

    Args:
        form_data: OAuth2PasswordRequestForm containing username and password.
        db: Database session.

    Returns:
        UserWithToken: The authenticated user and their JWT token.

    Raises:
        HTTPException: If authentication fails.
    """
    user_repository = UserRepository(db)
    service = UserService(user_repository)
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return UserWithToken(user=user, access_token=access_token, token_type="bearer")


@router.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve a list of all users.

    Args:
        db: Database session.

    Returns:
        List[UserResponse]: A list of user details.
    """
    user_repository = UserRepository(db)
    service = UserService(user_repository)
    return service.get_all_users()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve user details by user ID.

    Args:
        user_id: The ID of the user to retrieve.
        db: Database session.

    Returns:
        UserResponse: The user details.

    Raises:
        HTTPException: If the user is not found.
    """
    try:
        user_repository = UserRepository(db)
        service = UserService(user_repository)
        return service.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user by user ID.

    Args:
        user_id: The ID of the user to delete.
        db: Database session.

    Returns:
        dict: A message indicating successful deletion.

    Raises:
        HTTPException: If the user is not found.
    """
    user_repository = UserRepository(db)
    service = UserService(user_repository)
    if not service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update user details.

    Args:
        user_id: The ID of the user to update.
        user_update: UserUpdate model with updated user details.
        db: Database session.

    Returns:
        UserResponse: The updated user details.

    Raises:
        HTTPException: If the user is not found.
    """
    user_repository = UserRepository(db)
    service = UserService(user_repository)
    try:
        updated_user = service.update_user(user_id, user_update)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
