from datetime import date, timezone, datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.core.result import ServiceResult
from app.models.commit import Commit
from app.repositories import repository_repo
from app.repositories.snapshot_repo import snapshot_repo
from app.schemas.trend import TrendPoint, FolderTrendPoint, ViolationTrendPoint
from app.services.folder_coverage import FolderCoverageService
from app.services.merge_delay import MergeDelayService
from app.services.folder_health import FolderHealthService
from app.services.exception_detection import ExceptionDetectionService


class TrendAnalyticsService:
    """Service to capture daily governance state snapshots and compile historical trend metrics."""

    def __init__(
        self,
        coverage_service: Optional[FolderCoverageService] = None,
        delay_service: Optional[MergeDelayService] = None,
        health_service: Optional[FolderHealthService] = None,
        violation_service: Optional[ExceptionDetectionService] = None,
    ) -> None:
        self.coverage_service = coverage_service or FolderCoverageService()
        self.delay_service = delay_service or MergeDelayService()
        self.health_service = health_service or FolderHealthService()
        self.violation_service = violation_service or ExceptionDetectionService()

    async def capture_daily_snapshot(
        self, db: AsyncSession, repository_id: uuid.UUID, snapshot_date: Optional[date] = None
    ) -> ServiceResult[Dict[str, Any]]:
        """Aggregates all system metrics and records/upserts snapshot entries for the specified date."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        if not snapshot_date:
            snapshot_date = date.today()

        logger.info("Capturing daily metrics snapshot", repo_name=repo.name, snapshot_date=snapshot_date)

        # 1. Fetch metrics from coverage service
        cov_sum_res = await self.coverage_service.get_coverage_summary_data(db, repository_id)
        if cov_sum_res.is_failure:
            return ServiceResult.failure(cov_sum_res.error)
        coverage_summary = cov_sum_res.value

        missing_merges_res = await self.coverage_service.get_missing_merges_list(db, repository_id)
        if missing_merges_res.is_failure:
            return ServiceResult.failure(missing_merges_res.error)
        missing_merges = missing_merges_res.value

        # 2. Query total commits count from DB
        stmt_commits = select(func.count(Commit.id)).where(Commit.repository_id == repository_id)
        commits_res = await db.execute(stmt_commits)
        total_commits = commits_res.scalar() or 0

        # 3. Fetch violations summary
        viol_sum_res = await self.violation_service.get_violation_summary(db, repository_id)
        if viol_sum_res.is_failure:
            return ServiceResult.failure(viol_sum_res.error)
        violation_summary = viol_sum_res.value

        # 4. Fetch delay stats
        delay_stats_res = await self.delay_service.get_delay_statistics_data(db, repository_id)
        if delay_stats_res.is_failure:
            return ServiceResult.failure(delay_stats_res.error)
        delay_stats = delay_stats_res.value

        # 5. Fetch folder health details
        health_res = await self.health_service.compute_all_health(db, repository_id)
        if health_res.is_failure:
            return ServiceResult.failure(health_res.error)
        folder_health = health_res.value

        # Calculate composite governance score (average of folder health scores)
        if folder_health:
            gov_score = round(sum(f.health_score for f in folder_health) / len(folder_health), 2)
        else:
            gov_score = 100.0

        # 6. Upsert the overall snapshot
        snapshot_data = {
            "total_jiras": coverage_summary.total_jiras,
            "total_commits": total_commits,
            "overall_coverage_pct": coverage_summary.overall_coverage_pct,
            "missing_merge_count": len(missing_merges),
            "critical_violation_count": violation_summary.critical_count,
            "avg_delay_days": delay_stats.overall_avg_delay_days,
            "governance_score": gov_score,
            "metadata_info": {
                "high_violation_count": violation_summary.high_count,
                "medium_violation_count": violation_summary.medium_count,
                "low_violation_count": violation_summary.low_count
            }
        }
        await snapshot_repo.upsert_governance_snapshot(db, repository_id, snapshot_date, snapshot_data)

        # 7. Upsert individual folder health snapshots
        for fh in folder_health:
            fh_data = {
                "health_score": fh.health_score,
                "coverage_score": fh.coverage_score,
                "consistency_score": fh.consistency_score,
                "timeliness_score": fh.timeliness_score,
                "completeness_score": fh.completeness_score
            }
            await snapshot_repo.upsert_folder_health_snapshot(db, repository_id, snapshot_date, fh.folder_name, fh_data)

        await db.commit()
        logger.info("Successfully recorded repository snapshot", repository_id=repository_id, snapshot_date=snapshot_date)

        return ServiceResult.success({"status": "success", "date": snapshot_date})

    async def get_coverage_trend(
        self, db: AsyncSession, repository_id: uuid.UUID, days: int = 30
    ) -> ServiceResult[List[TrendPoint]]:
        """Compiles historical coverage percentage points."""
        snapshots = await snapshot_repo.get_governance_snapshots(db, repository_id, days=days)
        points = [
            TrendPoint(
                date=s.snapshot_date,
                value=float(s.overall_coverage_pct) if s.overall_coverage_pct is not None else 0.0
            )
            for s in snapshots
        ]
        return ServiceResult.success(points)

    async def get_delay_trend(
        self, db: AsyncSession, repository_id: uuid.UUID, days: int = 30
    ) -> ServiceResult[List[TrendPoint]]:
        """Compiles average merge delays history."""
        snapshots = await snapshot_repo.get_governance_snapshots(db, repository_id, days=days)
        points = [
            TrendPoint(
                date=s.snapshot_date,
                value=float(s.avg_delay_days) if s.avg_delay_days is not None else 0.0
            )
            for s in snapshots
        ]
        return ServiceResult.success(points)

    async def get_violation_trend(
        self, db: AsyncSession, repository_id: uuid.UUID, days: int = 30
    ) -> ServiceResult[List[ViolationTrendPoint]]:
        """Compiles daily counts of unresolved violations categorised by severity levels."""
        snapshots = await snapshot_repo.get_governance_snapshots(db, repository_id, days=days)
        points = []
        for s in snapshots:
            meta = s.metadata_info or {}
            high = meta.get("high_violation_count", 0)
            medium = meta.get("medium_violation_count", 0)
            low = meta.get("low_violation_count", 0)
            critical = s.critical_violation_count or 0
            points.append(
                ViolationTrendPoint(
                    date=s.snapshot_date,
                    critical_count=critical,
                    high_count=high,
                    medium_count=medium,
                    low_count=low,
                    total_count=critical + high + medium + low
                )
            )
        return ServiceResult.success(points)

    async def get_folder_health_trends(
        self, db: AsyncSession, repository_id: uuid.UUID, folder_name: Optional[str] = None, days: int = 30
    ) -> ServiceResult[List[FolderTrendPoint]]:
        """Compiles folder-specific health score parameters history."""
        snapshots = await snapshot_repo.get_folder_health_snapshots(db, repository_id, folder_name=folder_name, days=days)
        points = [
            FolderTrendPoint(
                date=s.snapshot_date,
                folder_name=s.folder_name,
                health_score=float(s.health_score) if s.health_score is not None else 0.0,
                coverage_score=float(s.coverage_score) if s.coverage_score is not None else 0.0,
                consistency_score=float(s.consistency_score) if s.consistency_score is not None else 0.0,
                timeliness_score=float(s.timeliness_score) if s.timeliness_score is not None else 0.0,
                completeness_score=float(s.completeness_score) if s.completeness_score is not None else 0.0
            )
            for s in snapshots
        ]
        return ServiceResult.success(points)
