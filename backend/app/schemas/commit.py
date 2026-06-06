from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel


class AuthorResponse(BaseModel):
    name: str
    email: str
    github_username: Optional[str] = None

    class Config:
        from_attributes = True


class CommitFileResponse(BaseModel):
    file_path: str
    folder: Optional[str] = None
    change_type: str
    additions: int
    deletions: int

    class Config:
        from_attributes = True


class CommitResponse(BaseModel):
    id: uuid.UUID
    sha: str
    repository_id: uuid.UUID
    branch: Optional[str] = None
    message: str
    commit_date: datetime
    ingested_at: datetime
    author: AuthorResponse

    class Config:
        from_attributes = True


class CommitDetailResponse(CommitResponse):
    files: List[CommitFileResponse] = []
    jiras: List[str] = []
