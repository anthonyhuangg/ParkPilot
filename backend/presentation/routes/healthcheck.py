from application.models.healthcheck import HealthcheckResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthcheck", response_model=HealthcheckResponse)
def healthcheck():
    return {"status": "healthy"}
