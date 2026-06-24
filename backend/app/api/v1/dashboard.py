import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.dashboard import (
    DashboardKPICard,
    DashboardSummary,
    GovernanceScoreDetail,
    RecentActivity,
)
from app.schemas.violation import RuleViolationResponse
from app.services.exception_detection import ExceptionDetectionService
from app.services.folder_coverage import FolderCoverageService
from app.services.governance_score import GovernanceScoreService
from app.services.merge_delay import MergeDelayService

router = APIRouter()


def _format_activity_description(log: AuditLog) -> str:
    """Formats raw audit logs into user-friendly description text."""
    action = log.action
    entity = log.entity_type

    if action == "login_success":
        return "Administrator successfully logged in to the dashboard."
    elif action == "login_failed":
        return f"Failed login attempt detected for user: {log.entity_id}."
    elif action == "sync_success":
        return "Repository commits and files sync completed successfully."
    elif action == "sync_failed":
        return "Repository synchronization task failed."
    elif action == "violation_acknowledged":
        return "Governance exception acknowledged by developer."

    return f"Action '{action}' executed on {entity or 'system'}."


@router.get("", response_model=ResponseEnvelope[DashboardSummary])
async def get_dashboard_summary(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve full aggregated dashboard summary details for a repository."""
    coverage_service = FolderCoverageService()
    delay_service = MergeDelayService()
    score_service = GovernanceScoreService()
    violation_service = ExceptionDetectionService()

    # 1. Fetch KPIs
    cov_sum_res = await coverage_service.get_coverage_summary_data(db, repository_id=repository_id)
    if cov_sum_res.is_failure:
        raise cov_sum_res.error
    coverage_summary = cov_sum_res.value

    delay_stats_res = await delay_service.get_delay_statistics_data(db, repository_id=repository_id)
    if delay_stats_res.is_failure:
        raise delay_stats_res.error
    delay_stats = delay_stats_res.value

    violations_summary_res = await violation_service.get_violation_summary(db, repository_id=repository_id)
    if violations_summary_res.is_failure:
        raise violations_summary_res.error
    violation_summary = violations_summary_res.value

    kpis = DashboardKPICard(
        total_jiras=coverage_summary.total_jiras,
        overall_coverage_pct=coverage_summary.overall_coverage_pct,
        avg_propagation_delay_days=delay_stats.overall_avg_delay_days,
        active_violations_count=violation_summary.total_violations
    )

    # 2. Fetch Governance Score
    score_res = await score_service.compute_repository_score(db, repository_id=repository_id)
    if score_res.is_failure:
        raise score_res.error
    governance_score = score_res.value

    # 3. Fetch Recent Activity from Audit Logs
    stmt_audit = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5)
    audit_res = await db.execute(stmt_audit)
    audit_logs = list(audit_res.scalars().all())

    recent_activity = [
        RecentActivity(
            id=log.id,
            timestamp=log.created_at,
            activity_type=log.action,
            description=_format_activity_description(log),
            details=log.details or {}
        )
        for log in audit_logs
    ]

    # 4. Fetch Critical active unacknowledged violations
    critical_violations_res = await violation_service.get_violations(
        db,
        repository_id=repository_id,
        severity="CRITICAL",
        is_acknowledged=False,
        is_resolved=False
    )
    critical_violations = critical_violations_res.value

    critical_items = [
        RuleViolationResponse.model_validate(v) for v in critical_violations
    ]

    summary = DashboardSummary(
        kpis=kpis,
        governance_score=governance_score,
        recent_activity=recent_activity,
        critical_items=critical_items
    )

    return ResponseEnvelope(success=True, data=summary)


@router.get("/kpis", response_model=ResponseEnvelope[DashboardKPICard])
async def get_dashboard_kpis(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch KPI metrics representing general repository governance stats."""
    coverage_service = FolderCoverageService()
    delay_service = MergeDelayService()
    violation_service = ExceptionDetectionService()

    cov_sum_res = await coverage_service.get_coverage_summary_data(db, repository_id=repository_id)
    if cov_sum_res.is_failure:
        raise cov_sum_res.error
    coverage_summary = cov_sum_res.value

    delay_stats_res = await delay_service.get_delay_statistics_data(db, repository_id=repository_id)
    if delay_stats_res.is_failure:
        raise delay_stats_res.error
    delay_stats = delay_stats_res.value

    violations_summary_res = await violation_service.get_violation_summary(db, repository_id=repository_id)
    if violations_summary_res.is_failure:
        raise violations_summary_res.error
    violation_summary = violations_summary_res.value

    kpis = DashboardKPICard(
        total_jiras=coverage_summary.total_jiras,
        overall_coverage_pct=coverage_summary.overall_coverage_pct,
        avg_propagation_delay_days=delay_stats.overall_avg_delay_days,
        active_violations_count=violation_summary.total_violations
    )
    return ResponseEnvelope(success=True, data=kpis)


@router.get("/governance-score", response_model=ResponseEnvelope[GovernanceScoreDetail])
async def get_repository_governance_score(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch composite score and grade detail for a repository."""
    score_service = GovernanceScoreService()
    score_res = await score_service.compute_repository_score(db, repository_id=repository_id)
    if score_res.is_failure:
        raise score_res.error
    return ResponseEnvelope(success=True, data=score_res.value)
