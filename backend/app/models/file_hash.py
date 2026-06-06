from datetime import datetime
import uuid
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, UUIDPrimaryKeyMixin


class FileHash(Base, UUIDPrimaryKeyMixin):
    """Database model for verifying file content consistency across target folders."""

    __tablename__ = "file_hashes"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    folder: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    last_commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    last_commit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    repository = relationship("Repository", back_populates="file_hashes")

    __table_args__ = (
        UniqueConstraint("repository_id", "file_path", "folder", name="uq_file_hashes_repo_path_folder"),
    )

    def __repr__(self) -> str:
        return f"<FileHash path={self.file_path} folder={self.folder} hash={self.sha256_hash[:8]}>"
