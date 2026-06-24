import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class RuleViolation(Base, UUIDPrimaryKeyMixin):
    """Database model for detected commit/merge governance violations."""

    __tablename__ = "rule_violations"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    jira_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    folder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="'{}'")

    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledge_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="violations")

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "rule_id",
            "jira_id",
            "folder_name",
            "file_path",
            name="uq_rule_violations_fields",
        ),
    )

    def __repr__(self) -> str:
        return f"<RuleViolation rule={self.rule_id} severity={self.severity} jira={self.jira_id}>"
