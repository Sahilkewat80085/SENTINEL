from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, HttpUrl


class RepositoryBase(BaseModel):
    name: str = Field(..., max_length=255, description="Unique repository configuration name")
    url: str = Field(..., description="Repository Git URL (https://... or git@...)")
    default_branch: str = Field(default="main", max_length=128)
    folders: List[str] = Field(default_factory=list, description="Target customer config folders")
    jira_patterns: List[str] = Field(
        default_factory=lambda: [r"[A-Z]{2,10}-\d{3,6}"],
        description="List of regex patterns to extract Jira IDs",
    )
    sync_mode: str = Field(default="api", max_length=20, description="api | git | hybrid")
    sync_interval: int = Field(default=30, description="Sync frequency in minutes")
    is_active: bool = Field(default=True)


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = None
    default_branch: Optional[str] = Field(None, max_length=128)
    folders: Optional[List[str]] = None
    jira_patterns: Optional[List[str]] = None
    sync_mode: Optional[str] = Field(None, max_length=20)
    sync_interval: Optional[int] = None
    is_active: Optional[bool] = None


class RepositoryResponse(RepositoryBase):
    id: uuid.UUID
    last_synced_at: Optional[datetime] = None
    last_sync_sha: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        # In pydantic v2, from_attributes replaces from_orm
