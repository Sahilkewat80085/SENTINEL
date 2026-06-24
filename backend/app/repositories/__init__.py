from app.models.repository import Repository
from app.repositories.audit_repo import audit_repo
from app.repositories.base import BaseRepository
from app.repositories.commit_repo import commit_repo
from app.repositories.report_repo import report_repo
from app.repositories.snapshot_repo import snapshot_repo
from app.repositories.user_repo import user_repo
from app.repositories.violation_repo import violation_repo

# Generic repositories for simple tables
repository_repo = BaseRepository(Repository)

__all__ = [
    "BaseRepository",
    "commit_repo",
    "repository_repo",
    "violation_repo",
    "snapshot_repo",
    "user_repo",
    "audit_repo",
    "report_repo",
]
