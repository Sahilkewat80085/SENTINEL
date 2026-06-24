import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.result import ServiceResult
from app.repositories import repository_repo
from app.schemas.delay import DelayResult, DelayStatistics, FolderDelayRank
from app.services.folder_coverage import FolderCoverageService


class MergeDelayService:
    """Service to compute merge delays, classifications, and environmental rankings."""

    def __init__(self, coverage_service: FolderCoverageService | None = None) -> None:
        self.coverage_service = coverage_service or FolderCoverageService()

    def _percentile(self, values: list[float], p: float) -> float:
        """Helper to calculate percentile value from a list of floats."""
        if not values:
            return 0.0
        sorted_val = sorted(values)
        k = (len(sorted_val) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_val[int(k)]
        d0 = sorted_val[int(f)] * (c - k)
        d1 = sorted_val[int(c)] * (k - f)
        return d0 + d1

    async def get_repository_delays(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[list[DelayResult]]:
        """Computes merge propagation delays and classifications for all repository Jiras."""
        matrix_res = await self.coverage_service.get_coverage_matrix_data(db, repository_id)
        if matrix_res.is_failure:
            return ServiceResult.failure(matrix_res.error)

        matrix = matrix_res.value
        rows = matrix.rows

        delay_results = []
        now = datetime.now(timezone.utc)

        for row in rows:
            # Map merge dates
            folder_merge_dates: dict[str, datetime | None] = {}
            valid_dates = []

            for f in row.folders:
                m_date = f.merge_date
                if m_date:
                    # Ensure timezone-aware
                    if m_date.tzinfo is None:
                        m_date = m_date.replace(tzinfo=timezone.utc)
                    valid_dates.append(m_date)
                    folder_merge_dates[f.folder_name] = m_date
                else:
                    folder_merge_dates[f.folder_name] = None

            if not valid_dates:
                continue

            # Earliest merge date acts as the initial commit date
            initial_commit_date = min(valid_dates)

            propagation_delay_days = None
            if row.status == "MERGED":
                latest_merge_date = max(valid_dates)
                propagation_delay_days = (latest_merge_date - initial_commit_date).total_seconds() / 86400.0

            # Classification rules:
            # If merged: use actual delay
            # If not merged: use elapsed time since initial commit to flag overdue merges!
            eval_days = propagation_delay_days
            if eval_days is None:
                eval_days = (now - initial_commit_date).total_seconds() / 86400.0

            if eval_days <= 3.0:
                status = "HEALTHY"
            elif eval_days <= 14.0:
                status = "WARNING"
            else:
                status = "CRITICAL"

            delay_results.append(
                DelayResult(
                    jira_id=row.jira_id,
                    initial_commit_date=initial_commit_date,
                    folder_merge_dates=folder_merge_dates,
                    propagation_delay_days=round(propagation_delay_days, 2) if propagation_delay_days is not None else None,
                    status=status
                )
            )

        return ServiceResult.success(delay_results)

    async def get_delay_statistics_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[DelayStatistics]:
        """Calculates aggregate delay metrics, classifications distribution, and folder rankings."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        delay_res = await self.get_repository_delays(db, repository_id)
        if delay_res.is_failure:
            return ServiceResult.failure(delay_res.error)

        delay_list = delay_res.value

        # Calculate general aggregates
        merged_delays = [d.propagation_delay_days for d in delay_list if d.propagation_delay_days is not None]
        avg_delay = (sum(merged_delays) / len(merged_delays)) if merged_delays else 0.0
        max_delay = max(merged_delays) if merged_delays else 0.0

        # Status distribution counts
        dist = {"HEALTHY": 0, "WARNING": 0, "CRITICAL": 0}
        for d in delay_list:
            dist[d.status] = dist.get(d.status, 0) + 1

        # Calculate per-folder delay metrics
        # For each folder, gather delay offsets from initial_commit_date
        folder_delays: dict[str, list[float]] = {}
        for folder in repo.folders or []:
            folder_delays[folder] = []

        for d in delay_list:
            init_date = d.initial_commit_date
            for folder_name, m_date in d.folder_merge_dates.items():
                if m_date and folder_name in folder_delays:
                    # Ensure tzinfo is resolved
                    if m_date.tzinfo is None:
                        m_date = m_date.replace(tzinfo=timezone.utc)
                    delay_offset = (m_date - init_date).total_seconds() / 86400.0
                    folder_delays[folder_name].append(delay_offset)

        folder_rankings: list[FolderDelayRank] = []
        for folder_name, offsets in folder_delays.items():
            if not offsets:
                continue

            folder_rankings.append(
                FolderDelayRank(
                    folder_name=folder_name,
                    avg_delay_days=round(sum(offsets) / len(offsets), 2),
                    max_delay_days=round(max(offsets), 2),
                    p95_delay_days=round(self._percentile(offsets, 95.0), 2)
                )
            )

        # Sort rankings: folders with highest average delay first (weakest targets)
        folder_rankings.sort(key=lambda x: x.avg_delay_days, reverse=True)

        stats = DelayStatistics(
            overall_avg_delay_days=round(avg_delay, 2),
            overall_max_delay_days=round(max_delay, 2),
            status_distribution=dist,
            folder_rankings=folder_rankings
        )
        return ServiceResult.success(stats)
