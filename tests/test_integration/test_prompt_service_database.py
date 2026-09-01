import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt
from app.repositories.prompt import PromptRepository
from app.schemas.prompt import PromptCreate
from app.services.prompt import PromptService


def create_prompt_service(
    session: AsyncSession,
) -> PromptService:
    """Create PromptService backed by a real database session."""

    repository = PromptRepository(session=session)

    return PromptService(
        session=session,
        repository=repository,
    )


@pytest.mark.asyncio
async def test_create_new_active_prompt_persists_prompt(
    db_session: AsyncSession,
) -> None:
    """Persist a newly created prompt in the database."""

    service = create_prompt_service(db_session)

    prompt_data = PromptCreate(
        name="Marketing Prompt",
        content="Generate professional social media content.",
    )

    created_prompt = await service.create_new_active_prompt(prompt_data)

    stmt = select(Prompt).where(Prompt.id == created_prompt.id)

    result = await db_session.execute(stmt)
    stored_prompt = result.scalar_one()

    assert stored_prompt.name == "Marketing Prompt"
    assert stored_prompt.content == ("Generate professional social media content.")
    assert stored_prompt.is_active is True


@pytest.mark.asyncio
async def test_create_new_active_prompt_deactivates_previous_prompt(
    db_session: AsyncSession,
) -> None:
    """Deactivate the previous active prompt."""

    old_prompt = Prompt(
        name="Old Prompt",
        content="This prompt was previously active.",
        is_active=True,
    )

    db_session.add(old_prompt)
    await db_session.commit()
    await db_session.refresh(old_prompt)

    service = create_prompt_service(db_session)

    new_prompt = await service.create_new_active_prompt(
        PromptCreate(
            name="New Prompt",
            content="This prompt should become active.",
        )
    )

    await db_session.refresh(old_prompt)

    assert old_prompt.is_active is False
    assert new_prompt.is_active is True


@pytest.mark.asyncio
async def test_only_one_prompt_remains_active_after_creation(
    db_session: AsyncSession,
) -> None:
    """Ensure exactly one prompt is active after creating a new one."""

    db_session.add_all(
        [
            Prompt(
                name="Prompt One",
                content="First historical prompt.",
                is_active=True,
            ),
            Prompt(
                name="Prompt Two",
                content="Second historical prompt.",
                is_active=True,
            ),
        ]
    )
    await db_session.commit()

    service = create_prompt_service(db_session)

    await service.create_new_active_prompt(
        PromptCreate(
            name="Prompt Three",
            content="The new active prompt.",
        )
    )

    stmt = select(func.count()).select_from(Prompt).where(Prompt.is_active.is_(True))

    result = await db_session.execute(stmt)

    active_count = result.scalar_one()

    assert active_count == 1


@pytest.mark.asyncio
async def test_prompt_name_must_be_unique(
    db_session: AsyncSession,
) -> None:
    """Reject duplicate prompt names at database level."""

    service = create_prompt_service(db_session)

    prompt_data = PromptCreate(
        name="Unique Prompt",
        content="Original prompt content.",
    )

    await service.create_new_active_prompt(prompt_data)

    duplicate_data = PromptCreate(
        name="Unique Prompt",
        content="Different content with the same name.",
    )

    with pytest.raises(IntegrityError):
        await service.create_new_active_prompt(duplicate_data)


@pytest.mark.asyncio
async def test_failed_duplicate_creation_rolls_back_transaction(
    db_session: AsyncSession,
) -> None:
    """Preserve database consistency after duplicate creation fails."""

    service = create_prompt_service(db_session)

    await service.create_new_active_prompt(
        PromptCreate(
            name="Existing Prompt",
            content="Existing prompt content.",
        )
    )

    with pytest.raises(IntegrityError):
        await service.create_new_active_prompt(
            PromptCreate(
                name="Existing Prompt",
                content="Duplicate prompt content.",
            )
        )

    stmt = select(Prompt)

    result = await db_session.execute(stmt)
    prompts = result.scalars().all()

    assert len(prompts) == 1
    assert prompts[0].name == "Existing Prompt"
    assert prompts[0].is_active is True


@pytest.mark.asyncio
async def test_created_prompt_has_timestamps(
    db_session: AsyncSession,
) -> None:
    """Populate timestamps when a prompt is created."""

    service = create_prompt_service(db_session)

    prompt = await service.create_new_active_prompt(
        PromptCreate(
            name="Timestamp Prompt",
            content="Prompt used to verify timestamps.",
        )
    )

    assert prompt.created_at is not None
    assert prompt.updated_at is not None
