from typing import Optional

from database.models.user import UserDatabaseModel
from sqlalchemy.orm import Session


class UserDatabase:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self, name: str, email: str, password_hash: str, role: str, car_reg: str
    ) -> UserDatabaseModel:
        user = UserDatabaseModel(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            car_reg=car_reg,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_users(self) -> list[type[UserDatabaseModel]]:
        return self.db.query(UserDatabaseModel).all()

    def get_user_by_id(self, id: int) -> Optional[UserDatabaseModel]:
        return (
            self.db.query(UserDatabaseModel).filter(UserDatabaseModel.id == id).first()
        )

    def get_user_by_email(self, email: str, include_password: bool = False):
        query = self.db.query(UserDatabaseModel).filter(
            UserDatabaseModel.email == email
        )

        if not include_password:
            query = query.with_entities(
                UserDatabaseModel.id,
                UserDatabaseModel.name,
                UserDatabaseModel.email,
                UserDatabaseModel.role,
                UserDatabaseModel.car_reg,
                UserDatabaseModel.created_at,
            )

        return query.first()
