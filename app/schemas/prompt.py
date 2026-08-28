from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PromptBase(BaseModel):
    """Define shared prompt properties."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The unique name of the prompt template.",
    )
    content: str = Field(
        ...,
        min_length=10,
        description="The system prompt instructions for the AI.",
    )


class PromptCreate(PromptBase):
    """Define data required to create a new prompt."""


class PromptResponse(PromptBase):
    """Represent a prompt returned by the API."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
