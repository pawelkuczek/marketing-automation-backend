from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
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


@pytest.mark.asyncio
async def test_get_prompts_returns_repository_results() -> None:
    """Return all prompts provided by the repository."""

    mock_session = create_mock_session()
    mock_repository = MagicMock()
    mock_repository.get_all = AsyncMock()

    prompts = [
        MagicMock(),
        MagicMock(),
    ]
    mock_repository.get_all.return_value = prompts

    service = PromptService(
        session=mock_session,
        repository=mock_repository,
    )

    result = await service.get_prompts()

    assert result == prompts
    mock_repository.get_all.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_get_prompt_raises_404_when_prompt_does_not_exist() -> None:
    """Raise 404 when the requested prompt does not exist."""

    mock_session = create_mock_session()
    mock_repository = MagicMock()
    mock_repository.get_by_id = AsyncMock(return_value=None)

    service = PromptService(
        session=mock_session,
        repository=mock_repository,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_prompt(999)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Prompt not found."

    mock_repository.get_by_id.assert_awaited_once_with(999)


@pytest.mark.asyncio
async def test_get_prompt_returns_existing_prompt() -> None:
    """Return an existing prompt by ID."""

    mock_session = create_mock_session()
    mock_repository = MagicMock()

    prompt = MagicMock()
    mock_repository.get_by_id = AsyncMock(return_value=prompt)

    service = PromptService(
        session=mock_session,
        repository=mock_repository,
    )

    result = await service.get_prompt(1)

    assert result is prompt
    mock_repository.get_by_id.assert_awaited_once_with(1)
