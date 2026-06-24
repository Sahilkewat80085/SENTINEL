import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryBase(BaseModel):
    name: str = Field(..., max_length=255, description="Unique repository configuration name")
    url: str = Field(..., description="Repository Git URL (https://... or git@...)")
    default_branch: str = Field(default="main", max_length=128)
    folders: list[str] = Field(default_factory=list, description="Target customer config folders")
    jira_patterns: list[str] = Field(
        default_factory=lambda: [r"[A-Z]{2,10}-\d{3,6}"],
        description="List of regex patterns to extract Jira IDs",
    )
    sync_mode: str = Field(default="api", max_length=20, description="api | git | hybrid")
    sync_interval: int = Field(default=30, description="Sync frequency in minutes")
    is_active: bool = Field(default=True)


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    url: str | None = None
    default_branch: str | None = Field(None, max_length=128)
    folders: list[str] | None = None
    jira_patterns: list[str] | None = None
    sync_mode: str | None = Field(None, max_length=20)
    sync_interval: int | None = None
    is_active: bool | None = None


class RepositoryResponse(RepositoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    last_synced_at: datetime | None = None
    last_sync_sha: str | None = None
    created_at: datetime
    updated_at: datetime
