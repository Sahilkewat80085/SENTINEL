from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class RuleViolationResponse(BaseModel):
    """Pydantic model representing a detailed database rule violation response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    rule_id: str
    severity: str
    category: str
    jira_id: Optional[str] = None
    folder_name: Optional[str] = None
    file_path: Optional[str] = None
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledge_note: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None


class ViolationAcknowledgeRequest(BaseModel):
    """Input parameters to acknowledge a governance violation."""

    acknowledge_note: Optional[str] = Field(None, description="Optional developer comments on the acknowledgement justification")


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
    by_category: Dict[str, int] = Field(default_factory=dict)
