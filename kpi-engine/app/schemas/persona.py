from typing import Any
from pydantic import BaseModel, Field


class PersonaRequest(BaseModel):
    role: str = Field(
        min_length=1,
        max_length=100,
        description="The persona or audience role to tailor the story for"
    )
    prompt: str = Field(
        min_length=1,
        max_length=2000
    )


class PersonaStoryPayload(BaseModel):
    role: str

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
    trace_id: str | None = None