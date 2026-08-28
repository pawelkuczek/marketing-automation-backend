from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.prompt import PromptCreate
from app.services.prompt import PromptService


def create_mock_session() -> MagicMock:
    """Create a mock AsyncSession with correctly typed sync and async methods."""

    session = MagicMock(spec=AsyncSession)

    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()

    return session


@pytest.mark.asyncio
async def test_create_new_active_prompt_deactivates_existing_prompts() -> None:
    """Deactivate existing prompts and persist the newly active prompt."""

    mock_session = create_mock_session()
    mock_repository = MagicMock()

    service = PromptService(
        session=mock_session,
        repository=mock_repository,
    )

    prompt_data = PromptCreate(
        name="Test Prompt",
        content="You are a helpful AI.",
    )

    result = await service.create_new_active_prompt(prompt_data)

    assert result.name == "Test Prompt"
    assert result.content == "You are a helpful AI."
    assert result.is_active is True

    mock_session.execute.assert_awaited_once()
    mock_session.add.assert_called_once_with(result)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_create_new_active_prompt_rolls_back_on_database_error() -> None:
    """Rollback the transaction when prompt creation fails."""

    mock_session = create_mock_session()
    mock_repository = MagicMock()

    mock_session.commit.side_effect = SQLAlchemyError("Database error")

    service = PromptService(
        session=mock_session,
        repository=mock_repository,
    )

    prompt_data = PromptCreate(
        name="Test Prompt",
        content="You are a helpful AI.",
    )

    with pytest.raises(SQLAlchemyError):
        await service.create_new_active_prompt(prompt_data)

    mock_session.rollback.assert_awaited_once()
