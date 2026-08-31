from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt
from app.repositories.prompt import PromptRepository
from app.schemas.prompt import PromptCreate, PromptUpdate


class PromptService:
    """Business logic layer for managing prompts."""

    def __init__(
        self,
        session: AsyncSession,
        repository: PromptRepository,
    ) -> None:
        self.session = session
        self.repository = repository

    async def get_prompts(self) -> Sequence[Prompt]:
        """Return all available prompts."""

        return await self.repository.get_all()

    async def get_prompt(self, prompt_id: int) -> Prompt:
        """Return a prompt by ID."""

        prompt = await self.repository.get_by_id(prompt_id)

        if prompt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found.",
            )

        return prompt

    async def update_prompt(
        self,
        prompt_id: int,
        prompt_data: PromptUpdate,
    ) -> Prompt:
        """Update editable properties of an existing prompt."""

        prompt = await self.get_prompt(prompt_id)

        update_data = prompt_data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        for field, value in update_data.items():
            setattr(prompt, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(prompt)

            return prompt

        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def activate_prompt(
        self,
        prompt_id: int,
    ) -> Prompt:
        """Make an existing prompt the active prompt."""

        prompt = await self.get_prompt(prompt_id)

        try:
            stmt = (
                update(Prompt).where(Prompt.is_active.is_(True)).values(is_active=False)
            )
            await self.session.execute(stmt)

            prompt.is_active = True

            await self.session.commit()
            await self.session.refresh(prompt)

            return prompt

        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_prompt(
        self,
        prompt_id: int,
    ) -> None:
        """Delete an inactive prompt."""

        prompt = await self.get_prompt(prompt_id)

        if prompt.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Active prompt cannot be deleted.",
            )

        try:
            await self.session.delete(prompt)
            await self.session.commit()

        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def create_new_active_prompt(
        self,
        prompt_data: PromptCreate,
    ) -> Prompt:
        """Create a new prompt and make it the active version."""

        try:
            stmt = (
                update(Prompt).where(Prompt.is_active.is_(True)).values(is_active=False)
            )
            await self.session.execute(stmt)

            new_prompt = Prompt(
                name=prompt_data.name,
                content=prompt_data.content,
                is_active=True,
            )

            self.session.add(new_prompt)

            await self.session.commit()
            await self.session.refresh(new_prompt)

            return new_prompt

        except SQLAlchemyError:
            await self.session.rollback()
            raise
