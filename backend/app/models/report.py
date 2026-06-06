from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class Report(Base, UUIDPrimaryKeyMixin):
    """Database model for tracking generated Excel and PDF governance reports."""

    __tablename__ = "reports"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EXCEL, PDF, FULL
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="'{}'")
    generated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report type={self.report_type} path={self.file_path} date={self.generated_at}>"
