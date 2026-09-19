from uuid import UUID

from pydantic import BaseModel


class AuthMeResponse(BaseModel):
    api_key_id: UUID
    name: str
