import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: str
    github_username: str | None = None


class CommitFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    file_path: str
    folder: str | None = None
    change_type: str
    additions: int
    deletions: int


class CommitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    sha: str
    repository_id: uuid.UUID
    branch: str | None = None
    message: str
    commit_date: datetime
    ingested_at: datetime
    author: AuthorResponse


class CommitDetailResponse(CommitResponse):
    files: list[CommitFileResponse] = []
    jiras: list[str] = []
