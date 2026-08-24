from decimal import Decimal
from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AIUsageLog(Base, TimestampMixin):
    """
    Track OpenAI API usage and associated costs.
    Provides data for usage monitoring and cost reporting.
    """

    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_file: Mapped[str] = mapped_column(String(255))
    model_used: Mapped[str] = mapped_column(String(50))
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    completion_tokens: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 5))

    def __repr__(self) -> str:
        return f"<AIUsageLog(id={self.id}, file='{self.target_file}', cost=${self.cost_usd})>"