from typing import List, Optional

from application.models.user import UserResponse
from database.models.user import UserDatabaseModel
from database.user_database import UserDatabase
from sqlalchemy.orm import Session


class UserRepository:
    """Repository for user data."""

    def __init__(self, db: Session):
        self.db_layer = UserDatabase(db)
        self.db = db

    def create_user(
        self, name: str, email: str, password_hash: str, role: str, car_reg: str
    ) -> UserResponse:
        database_response = self.db_layer.create_user(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            car_reg=car_reg,
        )
        return UserResponse.model_validate(database_response, from_attributes=True)

    def get_all_users(self) -> List[UserResponse]:
        database_responses = self.db_layer.get_all_users()
        return [
            UserResponse.model_validate(user, from_attributes=True)
            for user in database_responses
        ]

    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        database_response = self.db_layer.get_user_by_id(user_id)
        if not database_response:
            return None
        return UserResponse.model_validate(database_response, from_attributes=True)

    def get_user_by_email(self, email: str, include_password: bool = False):
        query = self.db.query(UserDatabaseModel).filter(
            UserDatabaseModel.email == email
        )
        user = query.first()
        if not user:
            return None
        if not include_password:
            user_dict = user.__dict__.copy()
            user_dict.pop("password_hash", None)
            return user_dict
        return user

    def get_db_user_by_email(self, email: str):
        return self.db_layer.get_user_by_email(email, include_password=True)

    def delete_user(self, user_id: int):
        user = self.db.query(UserDatabaseModel).filter_by(id=user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()

    def save(self, user: UserDatabaseModel):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
