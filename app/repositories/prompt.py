from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt


class PromptRepository:
    """
    Repository layer for managing Prompt database operations.
    Isolates SQLAlchemy specific logic from the service/router layers.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the repository with a database session.
        Dependency Injection will provide this session later.

        Args:
            session (AsyncSession): The asynchronous SQLAlchemy session.
        """

        self.session = session

    async def get_all(self) -> Sequence[Prompt]:
        """
        Retrieves all prompt templates from the database, ordered by creation date (newest first).

        Returns:
            Sequence[Prompt]: A collection of Prompt database objects.
        """

        stmt = select(Prompt).order_by(Prompt.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, prompt_id: int) -> Prompt | None:
        """
        Retrieves a specific prompt by its unique ID.

        Args:
            prompt_id (int): The unique identifier of the prompt.

        Returns:
            Prompt | None: The Prompt object if found, otherwise None.
        """

        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self) -> Prompt | None:
        """Return the currently active prompt."""

        stmt = select(Prompt).where(Prompt.is_active.is_(True))

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
