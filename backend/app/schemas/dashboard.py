import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.violation import RuleViolationResponse


class GovernanceScoreDetail(BaseModel):
    """Detailed breakdown of composite governance rating and letter grade."""

    model_config = ConfigDict(from_attributes=True)

    score: float = Field(..., description="Weighted composite score (0-100)")
    grade: str = Field(..., description="Letter grade (A, B, C, D, E, F)")
    folder_health_average: float = Field(..., description="Average health score across folders")
    violation_penalty: float = Field(..., description="Penalty score subtracted for unresolved issues")
    active_critical_count: int
    active_high_count: int
    active_medium_count: int
    active_low_count: int


class DashboardKPICard(BaseModel):
    """Top-level KPIs representing general workspace health."""

    total_jiras: int
    overall_coverage_pct: float
    avg_propagation_delay_days: float
    active_violations_count: int


class RecentActivity(BaseModel):
    """Representation of audit log and operational events on the dashboard feed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime
    activity_type: str  # e.g. "sync", "violation_detected", "violation_acknowledged"
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class DashboardSummary(BaseModel):
    """Composite payload aggregating all widgets for the home dashboard view."""

    kpis: DashboardKPICard
    governance_score: GovernanceScoreDetail
    recent_activity: list[RecentActivity] = Field(default_factory=list)
    critical_items: list[RuleViolationResponse] = Field(default_factory=list)
