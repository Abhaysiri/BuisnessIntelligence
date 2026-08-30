from typing import Any
from enum import Enum

from pydantic import BaseModel, Field


class PersonaRole(str, Enum):
    ANALYST = "analyst"
    FINANCE = "finance"
    EXECUTIVE = "executive"
    SALES = "sales"
    ENGINEERING = "engineering"


class PersonaRequest(BaseModel):
    role: PersonaRole
    prompt: str = Field(
        min_length=1,
        max_length=2000
    )


class PersonaStoryPayload(BaseModel):
    role: PersonaRole

    requested_focus: list[str] = Field(
        default_factory=list
    )

    headline: str
    narrative: str

    key_drivers: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]

    uncertainty: dict[str, Any]

    diagnostic_payload_id: str