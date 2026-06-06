from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FolderDelayRank(BaseModel):
    """Auditing delay rankings for an individual target environment folder."""

    folder_name: str
    avg_delay_days: float
    max_delay_days: float
    p95_delay_days: float


class DelayResult(BaseModel):
    """Calculated merge delays and classification for a single Jira ticket."""

    model_config = ConfigDict(from_attributes=True)

    jira_id: str
    initial_commit_date: datetime
    folder_merge_dates: Dict[str, Optional[datetime]] = Field(
        ..., description="Dates when the ticket was merged to each folder"
    )
    propagation_delay_days: Optional[float] = Field(
        None, description="Time in days between initial commit and latest merge"
    )
    status: str = Field(..., description="HEALTHY | WARNING | CRITICAL")


class DelayStatistics(BaseModel):
    """Aggregate statistics representing repository-wide propagation delay metrics."""

    overall_avg_delay_days: float
    overall_max_delay_days: float
    status_distribution: Dict[str, int] = Field(
        ..., description="Distribution count (e.g. {'HEALTHY': 10, ...})"
    )
    folder_rankings: List[FolderDelayRank] = Field(default_factory=list)
