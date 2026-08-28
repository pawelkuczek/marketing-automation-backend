from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt
from app.repositories.prompt import PromptRepository
from app.schemas.prompt import PromptCreate


class PromptService:
    """Business logic layer for managing prompts."""

    def __init__(
        self,
        session: AsyncSession,
        repository: PromptRepository,
    ) -> None:
        self.session = session
        self.repository = repository

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
