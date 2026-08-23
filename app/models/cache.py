from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SmartCache(Base, TimestampMixin):
    """
    Cache OpenAI API responses by cycle and topic.
    Prevents redundant API calls and reduces processing time and API costs.
    """

    __tablename__ = "smart_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle: Mapped[str] = mapped_column(String(100))
    topic: Mapped[str] = mapped_column(String(255))
    generated_content: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            "cycle",
              "topic",
                name="uq_smart_cache_cycle_topic"
        ),
    )

    def __repr__(self) -> str:
        return f"<SmartCache(id={self.id}, cycle='{self.cycle}', topic='{self.topic[:20]}...')>"