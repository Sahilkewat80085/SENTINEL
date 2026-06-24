import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class CommitJira(Base, UUIDPrimaryKeyMixin):
    """Database model for mappings between commits and Jira tickets."""

    __tablename__ = "commit_jiras"

    commit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    jira_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    commit = relationship("Commit", back_populates="jiras")

    __table_args__ = (
        UniqueConstraint("commit_id", "jira_id", name="uq_commit_jiras_commit_jira"),
    )

    def __repr__(self) -> str:
        return f"<CommitJira commit_id={self.commit_id} jira_id={self.jira_id}>"
