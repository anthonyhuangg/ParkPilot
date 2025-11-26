from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from application.models.carbon_saving import (
    CarbonSavingCreate,
    UserTotalSavingsResponse,
    LotSavingsSummary,
)
from application.services.carbon_saving_service import CarbonSavingService
from persistence.carbon_saving_repository import CarbonSavingRepository
from database import get_db

router = APIRouter(prefix="/carbon", tags=["carbon_saving"])


def get_carbon_saving_service(db: Session = Depends(get_db)):
    """Dependency injector for CarbonSavingService."""
    repo = CarbonSavingRepository(db)
    return CarbonSavingService(repo)


@router.post("/record-saving", status_code=status.HTTP_201_CREATED)
def record_carbon_saving(
    saving_data: CarbonSavingCreate,
    service: CarbonSavingService = Depends(get_carbon_saving_service),
):
    """
    Records a carbon saving event.
    Handles calculation exceptions so tests do not crash.
    """
    try:
        service.calculate_and_record_saving(saving_data)
        return {"message": "Carbon saving recorded successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to record saving: {e}")


@router.get(
    "/user/{user_id}",
    response_model=UserTotalSavingsResponse,
    description="Get the total lifetime carbon and money savings for a user.",
)
def get_user_savings_dashboard(
    user_id: int, service: CarbonSavingService = Depends(get_carbon_saving_service)
):
    """
    Allows a user to see the total carbon and money they have saved.
    """
    try:
        return service.get_user_dashboard(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch user savings: {e}"
        )


@router.get(
    "/operator/lot/{lot_id}",
    response_model=LotSavingsSummary,
    description="Get the total carbon/money saved for a specific lot on a \
        given date, including a list of contributors.",
)
def get_operator_savings_dashboard(
    lot_id: int,
    date: str = str(date.today()),
    service: CarbonSavingService = Depends(get_carbon_saving_service),
):
    """
    Allows a parking operator to see savings for an individual lot, \
        filtered by a specific date.
    - **lot_id**: The ID of the parking lot.
    - **date**: The date to filter by (format: YYYY-MM-DD). Defaults to today.
    """
    try:
        return service.get_operator_dashboard(lot_id, date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch operator savings: {e}"
        )
