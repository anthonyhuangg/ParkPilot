import logging
from persistence.carbon_saving_repository import CarbonSavingRepository
from application.models.carbon_saving import (
    CarbonSavingCreate,
    UserTotalSavingsResponse,
    LotSavingsSummary,
)
from fastapi import HTTPException
from datetime import datetime


logger = logging.getLogger("parkpilot.carbon_saving")


class CarbonSavingService:
    CO2_G_PER_M = 0.192
    MONEY_PER_KG_CO2_AUD = 0.05
    BASELINE_TIME_MIN = 5
    AVERAGE_SPEED_M_PER_MIN = 166.67  # 10 km/h

    def __init__(self, repository: CarbonSavingRepository):
        self.repository = repository

    def _convert_g_to_kg(self, grams: float) -> float:
        return grams / 1000.0

    def calculate_and_record_saving(self, saving_data: CarbonSavingCreate):
        """
        Calculates CO2 and money saved based on distance traveled and records the event.

        Args:
            saving_data (CarbonSavingCreate): Data containing user ID, lot ID
                and distance traveled.

        Returns:
            The created carbon saving record.
        """
        baseline_distance_m = self.BASELINE_TIME_MIN * self.AVERAGE_SPEED_M_PER_MIN
        distance_saved_m = max(0, baseline_distance_m - saving_data.distance_traveled_m)

        co2_saved_g = distance_saved_m * self.CO2_G_PER_M
        co2_saved_kg = self._convert_g_to_kg(co2_saved_g)
        money_saved_aud = co2_saved_kg * self.MONEY_PER_KG_CO2_AUD

        logger.info(
            f"Recording carbon saving for user {saving_data.user_id} \
                at lot {saving_data.lot_id}: "
            f"{co2_saved_g:.2f}g CO2 saved, ${money_saved_aud:.2f} AUD saved."
        )

        try:
            return self.repository.add_saving(
                user_id=saving_data.user_id,
                lot_id=saving_data.lot_id,
                distance_saved_m=distance_saved_m,
                co2_saved_g=co2_saved_g,
                money_saved_usd=money_saved_aud,  # Update field to AUD
            )
        except Exception as e:
            logger.error(f"Failed to record carbon saving: {e}")
            raise HTTPException(status_code=500, detail="Failed to record saving data.")

    def get_user_dashboard(self, user_id: int) -> UserTotalSavingsResponse:
        """
        Fetches the total lifetime carbon and money savings for a single user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            UserTotalSavingsResponse: The total savings for the user.
        """
        result = self.repository.get_total_user_savings(user_id)

        if not result or (
            result.total_co2_saved_g is None and result.total_money_saved_usd is None
        ):
            return UserTotalSavingsResponse(
                user_id=user_id, total_co2_saved_kg=0.0, total_money_saved_usd=0.0
            )

        total_co2_saved_kg = self._convert_g_to_kg(result.total_co2_saved_g or 0.0)
        total_money_saved_usd = result.total_money_saved_usd or 0.0

        return UserTotalSavingsResponse(
            user_id=user_id,
            total_co2_saved_kg=total_co2_saved_kg,
            total_money_saved_usd=total_money_saved_usd,
        )

    def get_operator_dashboard(self, lot_id: int, date_str: str) -> LotSavingsSummary:
        """
        Fetches carbon and money savings summary and \
            contributors for a lot on a specific date.

        Args:
            lot_id (int): The ID of the parking lot.
            date_str (str): The date in 'YYYY-MM-DD' format.

        Returns:
            LotSavingsSummary: The savings summary for the lot on the specified date.
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format, expected YYYY-MM-DD"
            )

        summary = self.repository.get_lot_savings_summary_by_date(lot_id, date_str)

        total_co2_g = (
            summary.total_co2_saved_g if summary and summary.total_co2_saved_g else 0.0
        )
        total_money_usd = (
            summary.total_money_saved_usd
            if summary and summary.total_money_saved_usd
            else 0.0
        )

        contributors = self.repository.get_lot_contributors_by_date(lot_id, date_str)

        return LotSavingsSummary(
            lot_id=lot_id,
            date=date_str,
            total_co2_saved_kg=self._convert_g_to_kg(total_co2_g),
            total_money_saved_usd=total_money_usd,
            contributors=contributors,
        )
