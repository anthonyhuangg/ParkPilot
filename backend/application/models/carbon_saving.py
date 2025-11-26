from pydantic import BaseModel, Field
from typing import List


class CarbonSavingCreate(BaseModel):
    user_id: int
    lot_id: int
    distance_traveled_m: float = Field(
        ..., gt=0, description="Distance (in meters) traveled by the user."
    )


class UserTotalSavingsResponse(BaseModel):
    user_id: int
    total_co2_saved_kg: float = Field(
        ..., description="Total CO2 saved by the user in kilograms."
    )
    total_money_saved_usd: float = Field(
        ..., description="Total money saved by the user."
    )


class ContributorSavings(BaseModel):
    user_id: int
    user_name: str
    total_co2_saved_kg: float
    total_money_saved_usd: float


class LotSavingsSummary(BaseModel):
    lot_id: int
    date: str
    total_co2_saved_kg: float = Field(
        ..., description="Total CO2 saved for this lot on the specified date."
    )
    total_money_saved_usd: float = Field(
        ..., description="Total money saved for this lot on the specified date."
    )
    contributors: List[ContributorSavings]
