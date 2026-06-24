from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Repository(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Database model for registered GitHub configurations."""

    __tablename__ = "repositories"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(128), default="main", server_default="main")

    # JSONB columns for lists
    folders: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="'[]'")
    jira_patterns: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="'[]'")

    sync_mode: Mapped[str] = mapped_column(String(20), default="api", server_default="api")
    sync_interval: Mapped[int] = mapped_column(Integer, default=30, server_default="30")

    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    file_hashes = relationship("FileHash", back_populates="repository", cascade="all, delete-orphan")
    violations = relationship("RuleViolation", back_populates="repository", cascade="all, delete-orphan")
    snapshots = relationship("GovernanceSnapshot", back_populates="repository", cascade="all, delete-orphan")
    folder_health_snapshots = relationship("FolderHealthSnapshot", back_populates="repository", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Repository name={self.name} url={self.url}>"
