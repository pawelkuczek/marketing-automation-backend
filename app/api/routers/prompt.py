from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.prompt import PromptRepository
from app.schemas.prompt import PromptCreate, PromptResponse
from app.services.prompt import PromptService

router = APIRouter(prefix="/prompts", tags=["Prompts"])


def get_prompt_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PromptService:
    """
    Dependency builder for PromptService.
    FastAPI will resolve the session dependency first, then pass it here.
    """

    repository = PromptRepository(session=session)

    return PromptService(
        session=session,
        repository=repository,
    )


@router.get(
    "",
    response_model=list[PromptResponse],
    summary="List all AI prompts",
)
async def get_prompts(
    service: Annotated[
        PromptService,
        Depends(get_prompt_service),
    ],
) -> list[PromptResponse]:
    """Return all available system prompts."""

    prompts = await service.get_prompts()

    return [PromptResponse.model_validate(prompt) for prompt in prompts]


@router.get(
    "/{prompt_id}",
    response_model=PromptResponse,
    summary="Get an AI prompt",
)
async def get_prompt(
    prompt_id: int,
    service: Annotated[
        PromptService,
        Depends(get_prompt_service),
    ],
) -> PromptResponse:
    """Return a system prompt by ID."""

    prompt = await service.get_prompt(prompt_id)

    return PromptResponse.model_validate(prompt)


@router.post(
    "",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new active AI Prompt",
    description=(
        "Adds a new prompt to the database and automatically "
        "deactivates the previously active one."
    ),
)
async def create_prompt(
    prompt_in: PromptCreate,
    service: Annotated[
        PromptService,
        Depends(get_prompt_service),
    ],
) -> PromptResponse:
    """Create a new active system prompt."""

    prompt = await service.create_new_active_prompt(prompt_in)

    return PromptResponse.model_validate(prompt)
