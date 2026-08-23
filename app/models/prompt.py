from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Prompt(Base, TimestampMixin):
    """
    Represent a system prompt used by the AI engine.
    Prompts can be managed dynamically without redeploying the application.
    """
    
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Prompt(id={self.id}, name='{self.name}', is_active={self.is_active})>"