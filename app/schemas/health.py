from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    """Response returned when the API process is alive."""

    status: Literal["alive"] = "alive"


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
