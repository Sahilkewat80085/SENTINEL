import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleViolationResponse(BaseModel):
    """Pydantic model representing a detailed database rule violation response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    rule_id: str
    severity: str
    category: str
    jira_id: str | None = None
    folder_name: str | None = None
    file_path: str | None = None
    description: str
    details: dict[str, Any] = Field(default_factory=dict)
    is_acknowledged: bool
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    acknowledge_note: str | None = None
    detected_at: datetime
    resolved_at: datetime | None = None


class ViolationAcknowledgeRequest(BaseModel):
    """Input parameters to acknowledge a governance violation."""

    acknowledge_note: str | None = Field(None, description="Optional developer comments on the acknowledgement justification")


class ViolationSummary(BaseModel):
    """Aggregate KPIs representing the overall violation state of the repository."""

    model_config = ConfigDict(from_attributes=True)

    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    acknowledged_count: int
    unacknowledged_count: int
    by_category: dict[str, int] = Field(default_factory=dict)
