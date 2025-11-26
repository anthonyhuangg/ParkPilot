from database.setup import Base
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func


class UserDatabaseModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    car_reg = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
