from fastapi import APIRouter, status

from app.schemas.health import LivenessResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check whether the API process is alive",
)
async def get_liveness() -> LivenessResponse:
    """Return successfully when the API process is running."""

    return LivenessResponse()
