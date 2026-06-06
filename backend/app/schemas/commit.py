from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: str
    github_username: Optional[str] = None


class CommitFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    file_path: str
    folder: Optional[str] = None
    change_type: str
    additions: int
    deletions: int


class CommitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    sha: str
    repository_id: uuid.UUID
    branch: Optional[str] = None
    message: str
    commit_date: datetime
    ingested_at: datetime
    author: AuthorResponse


class CommitDetailResponse(CommitResponse):
    files: List[CommitFileResponse] = []
    jiras: List[str] = []
