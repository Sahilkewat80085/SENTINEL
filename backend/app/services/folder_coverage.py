from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.core.result import ServiceResult
from app.repositories import repository_repo
from app.repositories.folder_repo import folder_repo
from app.schemas.coverage import (
    CoverageMatrix,
    CoverageSummary,
    FolderCoverageDetail,
    JiraCoverageRow,
    MissingMerge,
)


class FolderCoverageService:
    """Service handling folder coverage computations, matrix structuring, and summaries."""

    async def get_coverage_matrix_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[CoverageMatrix]:
        """Builds a complete matrix grid mapping Jiras to expected folders with status indicators."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        expected_folders = repo.folders or []
        if not expected_folders:
            return ServiceResult.success(
                CoverageMatrix(
                    repository_id=repository_id, folders_list=[], rows=[]
                )
            )

        # Fetch raw records from view
        raw_matrix = await folder_repo.get_coverage_matrix(db, repository_id)

        # Group by Jira ID
        jira_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in raw_matrix:
            jira_id = item["jira_id"]
            if jira_id not in jira_groups:
                jira_groups[jira_id] = []
            jira_groups[jira_id].append(item)

        rows: List[JiraCoverageRow] = []

        for jira_id, mappings in jira_groups.items():
            # Create a lookup mapping for quick access
            mapped_lookup = {m["expected_folder"]: m for m in mappings}

            folder_details: List[FolderCoverageDetail] = []
            merged_count = 0

            for folder in expected_folders:
                lookup = mapped_lookup.get(folder)
                is_merged = lookup["is_merged"] if lookup else False
                merge_date = lookup["merge_date"] if lookup else None

                if is_merged:
                    merged_count += 1

                folder_details.append(
                    FolderCoverageDetail(
                        folder_name=folder,
                        is_merged=is_merged,
                        merge_date=merge_date,
                    )
                )

            # Compute stats
            total_folders = len(expected_folders)
            coverage_pct = (merged_count / total_folders) * 100 if total_folders > 0 else 0.0

            if coverage_pct == 100.0:
                status = "MERGED"
            elif coverage_pct == 0.0:
                status = "MISSING"
            else:
                status = "PARTIAL"

            rows.append(
                JiraCoverageRow(
                    jira_id=jira_id,
                    folders=folder_details,
                    coverage_pct=round(coverage_pct, 2),
                    status=status,
                )
            )

        # Sort rows alphabetically by Jira ID
        rows.sort(key=lambda x: x.jira_id)

        matrix = CoverageMatrix(
            repository_id=repository_id,
            folders_list=expected_folders,
            rows=rows,
        )
        return ServiceResult.success(matrix)

    async def get_coverage_summary_data(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[CoverageSummary]:
        """Computes summary KPI indicators representing overall folder coverage metrics."""
        matrix_res = await self.get_coverage_matrix_data(db, repository_id)
        if matrix_res.is_failure:
            return ServiceResult.failure(matrix_res.error)

        matrix = matrix_res.value
        rows = matrix.rows

        total_jiras = len(rows)
        merged_count = sum(1 for r in rows if r.status == "MERGED")
        partial_count = sum(1 for r in rows if r.status == "PARTIAL")
        missing_count = sum(1 for r in rows if r.status == "MISSING")

        # Overall average coverage pct
        total_pct = sum(r.coverage_pct for r in rows)
        overall_coverage = (total_pct / total_jiras) if total_jiras > 0 else 100.0

        summary = CoverageSummary(
            total_jiras=total_jiras,
            merged_count=merged_count,
            partial_count=partial_count,
            missing_count=missing_count,
            overall_coverage_pct=round(overall_coverage, 2),
        )
        return ServiceResult.success(summary)

    async def get_missing_merges_list(
        self, db: AsyncSession, repository_id: Any
    ) -> ServiceResult[List[MissingMerge]]:
        """Compiles a flat list of folder targets that are missing updates for committed Jiras."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        raw_missing = await folder_repo.get_missing_merges_raw(db, repository_id)
        
        missing_merges = []
        for item in raw_missing:
            missing_merges.append(
                MissingMerge(
                    jira_id=item["jira_id"],
                    folder=item["folder"],
                    last_updated=item["last_updated"],
                )
            )

        return ServiceResult.success(missing_merges)
