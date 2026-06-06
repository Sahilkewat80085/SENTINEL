from app.models.repository import Repository
from app.repositories.base import BaseRepository
from app.repositories.commit_repo import commit_repo

# Generic repositories for simple tables
repository_repo = BaseRepository(Repository)

__all__ = [
    "BaseRepository",
    "commit_repo",
    "repository_repo",
]
