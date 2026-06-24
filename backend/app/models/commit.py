import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class Commit(Base, UUIDPrimaryKeyMixin):
    """Database model for ingested commits."""

    __tablename__ = "commits"

    sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("authors.id"), nullable=False, index=True
    )

    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    commit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )

    # Relationships
    repository = relationship("Repository", back_populates="commits")
    author = relationship("Author", back_populates="commits")
    files = relationship("CommitFile", back_populates="commit", cascade="all, delete-orphan")
    jiras = relationship("CommitJira", back_populates="commit", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("sha", "repository_id", name="uq_commits_sha_repository"),
    )

    def __repr__(self) -> str:
        return f"<Commit sha={self.sha} message={self.message[:30]}>"
