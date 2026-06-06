from typing import Any, List, Optional, Dict
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.trend import TrendPoint, FolderTrendPoint, ViolationTrendPoint
from app.services.trend_analytics import TrendAnalyticsService

router = APIRouter()


def parse_period_to_days(period: str) -> int:
    """Helper to convert query string periods (e.g. '7d', '12w', '30d') into day counts."""
    if not period:
        return 30
    period = period.strip().lower()
    try:
        if period.endswith("d"):
            return int(period[:-1])
        elif period.endswith("w"):
            return int(period[:-1]) * 7
        elif period.endswith("m"):
            return int(period[:-1]) * 30
        return int(period)
    except ValueError:
        return 30


@router.post("/snapshot", response_model=ResponseEnvelope[Dict[str, Any]])
async def trigger_manual_snapshot(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Manually trigger daily metrics snapshot capture for a repository."""
    service = TrendAnalyticsService()
    result = await service.capture_daily_snapshot(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/coverage", response_model=ResponseEnvelope[List[TrendPoint]])
async def get_coverage_trend(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    period: str = Query("30d", description="Trend window, e.g. 7d, 30d, 90d, 12w"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch historical coverage percentage points."""
    service = TrendAnalyticsService()
    days = parse_period_to_days(period)
    result = await service.get_coverage_trend(db, repository_id=repository_id, days=days)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/health", response_model=ResponseEnvelope[List[FolderTrendPoint]])
async def get_folder_health_trends(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    folder: Optional[str] = Query(None, description="Optional filter for specific folder"),
    period: str = Query("30d", description="Trend window, e.g. 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch folder-specific composite health metric history points."""
    service = TrendAnalyticsService()
    days = parse_period_to_days(period)
    result = await service.get_folder_health_trends(db, repository_id=repository_id, folder_name=folder, days=days)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/delay", response_model=ResponseEnvelope[List[TrendPoint]])
async def get_delay_trend(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    period: str = Query("30d", description="Trend window, e.g. 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch historical merge propagation delay averages history."""
    service = TrendAnalyticsService()
    days = parse_period_to_days(period)
    result = await service.get_delay_trend(db, repository_id=repository_id, days=days)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/violations", response_model=ResponseEnvelope[List[ViolationTrendPoint]])
async def get_violations_trend(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    period: str = Query("30d", description="Trend window, e.g. 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch historical counts of unresolved violations categorized by severity levels."""
    service = TrendAnalyticsService()
    days = parse_period_to_days(period)
    result = await service.get_violation_trend(db, repository_id=repository_id, days=days)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
