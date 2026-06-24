import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class CommitFile(Base, UUIDPrimaryKeyMixin):
    """Database model for individual files changed in a commit."""

    __tablename__ = "commit_files"

    commit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    folder: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ADDED, MODIFIED, DELETED, RENAMED

    additions: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    deletions: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    commit = relationship("Commit", back_populates="files")

    __table_args__ = (
        UniqueConstraint("commit_id", "file_path", name="uq_commit_files_commit_path"),
    )

    def __repr__(self) -> str:
        return f"<CommitFile path={self.file_path} folder={self.folder}>"
