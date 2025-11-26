from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    car_reg: str


class UserResponse(BaseModel):
    user_id: int = Field(..., alias="id")
    name: str
    email: str
    role: str
    car_reg: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    car_reg: str | None = None
