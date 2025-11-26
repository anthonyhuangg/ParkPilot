from datetime import datetime
from typing import List
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session

from database.models.carbon_saving import CarbonSaving
from database.models.user import UserDatabaseModel
from application.models.carbon_saving import ContributorSavings


class CarbonSavingRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_saving(
        self,
        user_id: int,
        lot_id: int,
        distance_saved_m: float,
        co2_saved_g: float,
        money_saved_usd: float,
    ):
        """Creates a new carbon saving record."""
        saving = CarbonSaving(
            user_id=user_id,
            lot_id=lot_id,
            route_length_saved_m=distance_saved_m,
            co2_saved_g=co2_saved_g,
            money_saved_usd=money_saved_usd,
        )
        self.db.add(saving)
        self.db.commit()
        self.db.refresh(saving)
        return saving

    def get_total_user_savings(self, user_id: int):
        """Aggregates total savings for a specific user."""
        result = (
            self.db.query(
                func.sum(CarbonSaving.co2_saved_g).label("total_co2_saved_g"),
                func.sum(CarbonSaving.money_saved_usd).label("total_money_saved_usd"),
            )
            .filter(CarbonSaving.user_id == user_id)
            .one_or_none()
        )
        return result

    def get_lot_savings_summary_by_date(self, lot_id: int, date_str: str):
        """Aggregates total lot savings for a specific date."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        query = self.db.query(
            func.sum(CarbonSaving.co2_saved_g).label("total_co2_saved_g"),
            func.sum(CarbonSaving.money_saved_usd).label("total_money_saved_usd"),
        ).filter(
            and_(
                CarbonSaving.lot_id == lot_id,
                extract("year", CarbonSaving.date_time) == date_obj.year,
                extract("month", CarbonSaving.date_time) == date_obj.month,
                extract("day", CarbonSaving.date_time) == date_obj.day,
            )
        )
        return query.one_or_none()

    def get_lot_contributors_by_date(
        self, lot_id: int, date_str: str
    ) -> List[ContributorSavings]:
        """Lists contributors and their individual savings for a \
            specific lot and date."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        results = (
            self.db.query(
                UserDatabaseModel.id,
                UserDatabaseModel.name,
                func.sum(CarbonSaving.co2_saved_g).label("total_co2_saved_g"),
                func.sum(CarbonSaving.money_saved_usd).label("total_money_saved_usd"),
            )
            .join(CarbonSaving, CarbonSaving.user_id == UserDatabaseModel.id)
            .filter(
                and_(
                    CarbonSaving.lot_id == lot_id,
                    extract("year", CarbonSaving.date_time) == date_obj.year,
                    extract("month", CarbonSaving.date_time) == date_obj.month,
                    extract("day", CarbonSaving.date_time) == date_obj.day,
                )
            )
            .group_by(UserDatabaseModel.id, UserDatabaseModel.name)
            .order_by(func.sum(CarbonSaving.co2_saved_g).desc())
            .all()
        )

        contributors_list = []
        for user_id, user_name, co2_g, money_usd in results:
            contributors_list.append(
                ContributorSavings(
                    user_id=user_id,
                    user_name=user_name,
                    total_co2_saved_kg=co2_g / 1000,
                    total_money_saved_usd=money_usd,
                )
            )
        return contributors_list
