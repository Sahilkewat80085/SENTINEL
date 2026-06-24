from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class Author(Base, UUIDPrimaryKeyMixin):
    """Database model for commit authors."""

    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )

    # Relationships
    commits = relationship("Commit", back_populates="author")

    def __repr__(self) -> str:
        return f"<Author name={self.name} email={self.email}>"
