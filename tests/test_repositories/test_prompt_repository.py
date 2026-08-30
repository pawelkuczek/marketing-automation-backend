from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt
from app.repositories.prompt import PromptRepository


@pytest.mark.asyncio
async def test_get_by_id_returns_existing_prompt(
    db_session: AsyncSession,
) -> None:
    """Return a prompt when a matching ID exists."""

    prompt = Prompt(
        name="Existing Prompt",
        content="This is an existing prompt.",
        is_active=True,
    )

    db_session.add(prompt)
    await db_session.commit()
    await db_session.refresh(prompt)

    repository = PromptRepository(session=db_session)

    result = await repository.get_by_id(prompt.id)

    assert result is not None
    assert result.id == prompt.id
    assert result.name == "Existing Prompt"
    assert result.content == "This is an existing prompt."
    assert result.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing_prompt(
    db_session: AsyncSession,
) -> None:
    """Return None when the requested prompt does not exist."""

    repository = PromptRepository(session=db_session)

    result = await repository.get_by_id(999_999)

    assert result is None


@pytest.mark.asyncio
async def test_get_all_returns_prompts_ordered_by_created_at_desc(
    db_session: AsyncSession,
) -> None:
    """Return prompts ordered from newest to oldest."""

    now = datetime.now(timezone.utc)

    oldest_prompt = Prompt(
        name="Old Prompt",
        content="This is the oldest prompt.",
        is_active=False,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )

    middle_prompt = Prompt(
        name="Middle Prompt",
        content="This is the middle prompt.",
        is_active=False,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )

    newest_prompt = Prompt(
        name="New Prompt",
        content="This is the newest prompt.",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db_session.add_all(
        [
            oldest_prompt,
            newest_prompt,
            middle_prompt,
        ]
    )

    await db_session.commit()

    repository = PromptRepository(session=db_session)

    result = await repository.get_all()

    assert [prompt.name for prompt in result] == [
        "New Prompt",
        "Middle Prompt",
        "Old Prompt",
    ]


@pytest.mark.asyncio
async def test_get_active_returns_active_prompt(
    db_session: AsyncSession,
) -> None:
    """Return the currently active prompt."""

    inactive_prompt = Prompt(
        name="Inactive Prompt",
        content="Historical prompt content.",
        is_active=False,
    )

    active_prompt = Prompt(
        name="Active Prompt",
        content="Current prompt content.",
        is_active=True,
    )

    db_session.add_all(
        [
            inactive_prompt,
            active_prompt,
        ]
    )
    await db_session.commit()

    repository = PromptRepository(session=db_session)

    result = await repository.get_active()

    assert result is not None
    assert result.id == active_prompt.id
    assert result.name == "Active Prompt"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_get_active_returns_none_when_no_active_prompt(
    db_session: AsyncSession,
) -> None:
    """Return None when no active prompt exists."""

    repository = PromptRepository(session=db_session)

    result = await repository.get_active()

    assert result is None
