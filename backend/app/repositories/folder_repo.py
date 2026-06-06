from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger


class FolderRepository:
    """Repository handling folder coverage calculations, matrix, and missing merges."""

    async def refresh_coverage_matrix_view(self, db: AsyncSession) -> None:
        """Refreshes the mv_coverage_matrix materialized view, falling back to standard refresh if concurrent fails."""
        try:
            logger.info("Refreshing mv_coverage_matrix materialized view concurrently")
            await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_coverage_matrix"))
            await db.commit()
        except Exception as e:
            logger.warn("Failed concurrent refresh of mv_coverage_matrix, doing standard refresh", error=str(e))
            try:
                await db.execute(text("REFRESH MATERIALIZED VIEW mv_coverage_matrix"))
                await db.commit()
            except Exception as ex:
                logger.error("Failed standard refresh of mv_coverage_matrix", error=str(ex))
                await db.rollback()

    async def get_coverage_matrix(self, db: AsyncSession, repository_id: Any) -> List[Dict[str, Any]]:
        """Queries the coverage matrix for a repository from mv_coverage_matrix."""
        try:
            test_query = text("SELECT 1 FROM mv_coverage_matrix LIMIT 1")
            await db.execute(test_query)
        except Exception:
            await self.refresh_coverage_matrix_view(db)

        query = """
            SELECT jira_id, expected_folder, is_merged, merge_date
            FROM mv_coverage_matrix
            WHERE repository_id = :repository_id
            ORDER BY jira_id, expected_folder
        """
        res = await db.execute(text(query), {"repository_id": repository_id})
        rows = res.all()

        results = []
        for r in rows:
            results.append({
                "jira_id": r.jira_id,
                "expected_folder": r.expected_folder,
                "is_merged": r.is_merged,
                "merge_date": r.merge_date
            })
        return results

    async def get_missing_merges_raw(self, db: AsyncSession, repository_id: Any) -> List[Dict[str, Any]]:
        """Queries rows that are missing merges (expected but not merged) from mv_coverage_matrix."""
        try:
            test_query = text("SELECT 1 FROM mv_coverage_matrix LIMIT 1")
            await db.execute(test_query)
        except Exception:
            await self.refresh_coverage_matrix_view(db)

        query = """
            SELECT m.jira_id, m.expected_folder AS folder, s.last_updated
            FROM mv_coverage_matrix m
            JOIN mv_jira_summary s ON s.jira_id = m.jira_id AND s.repository_id = m.repository_id
            WHERE m.repository_id = :repository_id AND m.is_merged = false
            ORDER BY s.last_updated DESC, m.jira_id, m.expected_folder
        """
        res = await db.execute(text(query), {"repository_id": repository_id})
        rows = res.all()

        results = []
        for r in rows:
            results.append({
                "jira_id": r.jira_id,
                "folder": r.folder,
                "last_updated": r.last_updated
            })
        return results


# Singleton instance
folder_repo = FolderRepository()
