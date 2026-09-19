from fastapi import APIRouter, status

from app.core.exceptions import AppError
from app.db.session import check_database_connection
from app.schemas.health import LivenessResponse, ReadinessResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
)
async def liveness() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
)
async def readiness() -> ReadinessResponse:
    try:
        await check_database_connection()
    except Exception as exc:
        raise AppError(
            code="DATABASE_UNAVAILABLE",
            message="Database is unavailable.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        ) from exc

    return ReadinessResponse(status="ready")
