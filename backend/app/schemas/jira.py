import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JiraSummary(BaseModel):
    """Schema representing an aggregated Jira ticket status."""

    model_config = ConfigDict(from_attributes=True)

    jira_id: str = Field(..., description="Jira issue key (e.g. NC-4928)")
    repository_id: uuid.UUID
    commit_count: int
    author_count: int
    first_seen: datetime
    last_updated: datetime
    touched_folders: list[str] = Field(default_factory=list)
    folder_count: int
    status: str = Field(..., description="ACTIVE | STALE | DORMANT | ARCHIVED")


class JiraTimelineItem(BaseModel):
    """Individual commit item on a Jira issue's merge timeline."""

    sha: str
    message: str
    commit_date: datetime
    author_name: str
    author_email: str
    folders: list[str]
    files_count: int


class JiraDetail(BaseModel):
    """Comprehensive details for a Jira ticket including its timeline."""

    summary: JiraSummary
    timeline: list[JiraTimelineItem]
