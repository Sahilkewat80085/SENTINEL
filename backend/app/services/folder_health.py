from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.result import ServiceResult
from app.models.file_hash import FileHash
from app.repositories import repository_repo
from app.schemas.folder import FolderHealthRank, FolderHealthResult, HeatmapCell
from app.services.content_verification import ContentVerificationService
from app.services.folder_coverage import FolderCoverageService
from app.services.merge_delay import MergeDelayService


class FolderHealthService:
    """Service to compute folder health metrics, rankings, and heatmap data."""

    def __init__(
        self,
        coverage_service: FolderCoverageService | None = None,
        content_service: ContentVerificationService | None = None,
        delay_service: MergeDelayService | None = None,
    ) -> None:
        self.coverage_service = coverage_service or FolderCoverageService()
        self.content_service = content_service or ContentVerificationService()
        self.delay_service = delay_service or MergeDelayService()

    def _classify_health(self, score: float) -> str:
        """Classifies a health score into standard bands."""
        if score >= 90.0:
            return "EXCELLENT"
        elif score >= 70.0:
            return "GOOD"
        elif score >= 50.0:
            return "WARNING"
        elif score >= 25.0:
            return "POOR"
        else:
            return "CRITICAL"

    async def compute_all_health(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[list[FolderHealthResult]]:
        """Computes composite health scores for all configured folders in the repository."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        folders = repo.folders or []
        if not folders:
            return ServiceResult.success([])

        # 1. Fetch coverage matrix data
        coverage_res = await self.coverage_service.get_coverage_matrix_data(db, repository_id)
        if coverage_res.is_failure:
            return ServiceResult.failure(coverage_res.error)
        matrix = coverage_res.value
        rows = matrix.rows
        total_jiras = len(rows)

        # 2. Fetch content drift report
        drift_res = await self.content_service.get_drift_report_data(db, repository_id)
        if drift_res.is_failure:
            return ServiceResult.failure(drift_res.error)
        drift_report = drift_res.value

        # 3. Fetch merge delay statistics
        delay_stats_res = await self.delay_service.get_delay_statistics_data(db, repository_id)
        if delay_stats_res.is_failure:
            return ServiceResult.failure(delay_stats_res.error)
        delay_stats = delay_stats_res.value

        # 4. Fetch database statistics for folder file counts and total distinct files
        stmt_counts = (
            select(FileHash.folder, func.count(FileHash.id))
            .where(FileHash.repository_id == repository_id)
            .group_by(FileHash.folder)
        )
        counts_res = await db.execute(stmt_counts)
        folder_file_counts = {row[0]: row[1] for row in counts_res.all()}

        stmt_unique = select(func.count(func.distinct(FileHash.file_path))).where(FileHash.repository_id == repository_id)
        unique_res = await db.execute(stmt_unique)
        files_expected = unique_res.scalar() or 0

        # Calculate scores for each folder
        # Initialize calculations helper maps
        folder_divergent_counts: dict[str, int] = dict.fromkeys(folders, 0)
        for drifted_file in drift_report.drifted_files:
            for f in drifted_file.divergent_folders:
                if f in folder_divergent_counts:
                    folder_divergent_counts[f] += 1

        folder_avg_delays = {r.folder_name: r.avg_delay_days for r in delay_stats.folder_rankings}

        results = []
        for folder in folders:
            # Metric A: Coverage (35% weight)
            if total_jiras == 0:
                coverage_score = 100.0
            else:
                merged_jiras = sum(
                    1 for r in rows
                    for f in r.folders
                    if f.folder_name == folder and f.is_merged
                )
                coverage_score = round((merged_jiras / total_jiras) * 100.0, 2)

            # Metric B: Consistency (30% weight)
            total_files = folder_file_counts.get(folder, 0)
            if total_files == 0:
                consistency_score = 100.0
            else:
                divergent_count = folder_divergent_counts.get(folder, 0)
                identical_files = max(0, total_files - divergent_count)
                consistency_score = round((identical_files / total_files) * 100.0, 2)

            # Metric C: Timeliness (20% weight)
            avg_delay = folder_avg_delays.get(folder)
            if avg_delay is None:
                timeliness_score = 100.0
            else:
                timeliness_score = round(max(0.0, 100.0 - (avg_delay * 3.0)), 2)

            # Metric D: Completeness (15% weight)
            if files_expected == 0:
                completeness_score = 100.0
            else:
                completeness_score = round((total_files / files_expected) * 100.0, 2)

            # Weighted formula:
            health_score = round(
                coverage_score * 0.35 +
                consistency_score * 0.30 +
                timeliness_score * 0.20 +
                completeness_score * 0.15,
                2
            )

            classification = self._classify_health(health_score)

            results.append(
                FolderHealthResult(
                    folder_name=folder,
                    coverage_score=coverage_score,
                    consistency_score=consistency_score,
                    timeliness_score=timeliness_score,
                    completeness_score=completeness_score,
                    health_score=health_score,
                    classification=classification
                )
            )

        return ServiceResult.success(results)

    async def compute_health(
        self, db: AsyncSession, repository_id: Any, folder: str
    ) -> ServiceResult[FolderHealthResult]:
        """Computes health score details for a specific folder."""
        all_res = await self.compute_all_health(db, repository_id)
        if all_res.is_failure:
            return ServiceResult.failure(all_res.error)

        for item in all_res.value:
            if item.folder_name == folder:
                return ServiceResult.success(item)

        return ServiceResult.failure(EntityNotFoundException("Folder", folder))

    async def get_health_ranking(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[list[FolderHealthRank]]:
        """Ranks all repository folders by their health score (highest first)."""
        all_res = await self.compute_all_health(db, repository_id)
        if all_res.is_failure:
            return ServiceResult.failure(all_res.error)

        # Sort folders by health score descending (strongest folders first)
        sorted_folders = sorted(all_res.value, key=lambda x: x.health_score, reverse=True)

        rankings = []
        for i, item in enumerate(sorted_folders):
            rankings.append(
                FolderHealthRank(
                    folder_name=item.folder_name,
                    health_score=item.health_score,
                    classification=item.classification,
                    rank=i + 1
                )
            )

        return ServiceResult.success(rankings)

    async def get_weakest_folders(
        self, db: AsyncSession, repository_id: Any, n: int = 3
    ) -> ServiceResult[list[FolderHealthResult]]:
        """Returns the weakest N folders in the repository based on health score (lowest first)."""
        all_res = await self.compute_all_health(db, repository_id)
        if all_res.is_failure:
            return ServiceResult.failure(all_res.error)

        # Sort folders by health score ascending (weakest folders first)
        sorted_folders = sorted(all_res.value, key=lambda x: x.health_score)
        return ServiceResult.success(sorted_folders[:n])

    async def get_heatmap_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[list[HeatmapCell]]:
        """Generates flat heatmap representation for all metric scores per folder."""
        all_res = await self.compute_all_health(db, repository_id)
        if all_res.is_failure:
            return ServiceResult.failure(all_res.error)

        cells = []
        for item in all_res.value:
            cells.append(HeatmapCell(folder_name=item.folder_name, metric="coverage", score=item.coverage_score))
            cells.append(HeatmapCell(folder_name=item.folder_name, metric="consistency", score=item.consistency_score))
            cells.append(HeatmapCell(folder_name=item.folder_name, metric="timeliness", score=item.timeliness_score))
            cells.append(HeatmapCell(folder_name=item.folder_name, metric="completeness", score=item.completeness_score))
            cells.append(HeatmapCell(folder_name=item.folder_name, metric="health", score=item.health_score))

        return ServiceResult.success(cells)
