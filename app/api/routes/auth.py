from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_authenticated_api_key
from app.schemas.auth import AuthMeResponse
from app.services.authentication_service import AuthenticatedApiKey

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
)


@router.get("/me", response_model=AuthMeResponse)
async def get_auth_identity(
    identity: Annotated[
        AuthenticatedApiKey,
        Depends(get_authenticated_api_key),
    ],
) -> AuthMeResponse:
    return AuthMeResponse(
        api_key_id=identity.id,
        name=identity.name,
    )
