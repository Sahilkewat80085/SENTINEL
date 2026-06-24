import uuid
from datetime import date
from typing import Any

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class GovernanceSnapshot(Base, UUIDPrimaryKeyMixin):
    """Database model for repository-wide daily snapshots."""

    __tablename__ = "governance_snapshots"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    total_jiras: Mapped[int] = mapped_column(Integer, nullable=False)
    total_commits: Mapped[int] = mapped_column(Integer, nullable=False)

    overall_coverage_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    missing_merge_count: Mapped[int] = mapped_column(Integer, nullable=True)
    critical_violation_count: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_delay_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)
    governance_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)

    metadata_info: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="'{}'"
    )

    # Relationships
    repository = relationship("Repository", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint("repository_id", "snapshot_date", name="uq_gov_snapshots_repo_date"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceSnapshot date={self.snapshot_date} score={self.governance_score}>"


class FolderHealthSnapshot(Base, UUIDPrimaryKeyMixin):
    """Database model for folder-specific daily health snapshots."""

    __tablename__ = "folder_health_snapshots"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    folder_name: Mapped[str] = mapped_column(String(255), nullable=False)

    health_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    coverage_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    consistency_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    timeliness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    completeness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="folder_health_snapshots")

    __table_args__ = (
        UniqueConstraint("repository_id", "snapshot_date", "folder_name", name="uq_folder_snapshots_repo_date_folder"),
    )

    def __repr__(self) -> str:
        return f"<FolderHealthSnapshot folder={self.folder_name} date={self.snapshot_date} score={self.health_score}>"
