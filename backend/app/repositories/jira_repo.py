from typing import Any

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.author import Author
from app.models.commit import Commit
from app.models.commit_jira import CommitJira


class JiraRepository:
    """Repository class for Jira ticket aggregations, view refreshes, and timelines."""

    async def refresh_jira_summary_view(self, db: AsyncSession) -> None:
        """Refreshes the mv_jira_summary materialized view concurrently if possible, falling back to standard refresh."""
        try:
            logger.info("Refreshing mv_jira_summary materialized view concurrently")
            await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_jira_summary"))
            await db.commit()
        except Exception as e:
            logger.warn("Failed concurrent refresh, performing standard refresh", error=str(e))
            # Fallback to standard refresh (required if view was never populated)
            try:
                await db.execute(text("REFRESH MATERIALIZED VIEW mv_jira_summary"))
                await db.commit()
            except Exception as ex:
                logger.error("Failed standard refresh of mv_jira_summary", error=str(ex))
                await db.rollback()

    async def get_jira_summaries(
        self,
        db: AsyncSession,
        *,
        repository_id: Any | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Queries pre-computed summaries from the mv_jira_summary materialized view."""
        # Check if the view is populated by attempting a select. If it fails, refresh first.
        try:
            test_query = text("SELECT 1 FROM mv_jira_summary LIMIT 1")
            await db.execute(test_query)
        except Exception:
            # View is likely unpopulated/stale, refresh it
            await self.refresh_jira_summary_view(db)

        # Build search query
        conditions = []
        params = {"limit": limit, "offset": skip}

        if repository_id:
            conditions.append("repository_id = :repository_id")
            params["repository_id"] = repository_id
        if search:
            conditions.append("jira_id ILIKE :search")
            params["search"] = f"%{search}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query_str = f"""
            SELECT jira_id, repository_id, commit_count, author_count, first_seen, last_updated, touched_folders, folder_count
            FROM mv_jira_summary
            {where_clause}
            ORDER BY last_updated DESC
            LIMIT :limit OFFSET :offset
        """

        count_str = f"""
            SELECT COUNT(*) FROM mv_jira_summary {where_clause}
        """

        res = await db.execute(text(query_str), params)
        rows = res.all()

        count_res = await db.execute(text(count_str), params)
        total = count_res.scalar() or 0

        # Convert Row objects to dictionaries
        summaries = []
        for r in rows:
            summaries.append({
                "jira_id": r.jira_id,
                "repository_id": r.repository_id,
                "commit_count": r.commit_count,
                "author_count": r.author_count,
                "first_seen": r.first_seen,
                "last_updated": r.last_updated,
                "touched_folders": r.touched_folders or [],
                "folder_count": r.folder_count,
            })

        return summaries, total

    async def get_jira_timeline(self, db: AsyncSession, jira_id: str, repository_id: Any) -> list[dict[str, Any]]:
        """Returns chronological list of commits for a Jira ID across target folders."""
        query = (
            select(Commit)
            .join(CommitJira)
            .join(Author)
            .where(
                and_(
                    CommitJira.jira_id == jira_id,
                    Commit.repository_id == repository_id
                )
            )
            .options(
                # Eagerly load files and authors to prevent lazy-load session detach errors
                selectinload(Commit.author),
                selectinload(Commit.files)
            )
            .order_by(Commit.commit_date.asc())
        )

        res = await db.execute(query)
        commits = res.scalars().all()

        timeline = []
        for c in commits:
            folders_touched = list({f.folder for f in c.files if f.folder})
            timeline.append({
                "sha": c.sha,
                "message": c.message,
                "commit_date": c.commit_date,
                "author_name": c.author.name,
                "author_email": c.author.email,
                "folders": folders_touched,
                "files_count": len(c.files),
            })

        return timeline


# Singleton instance
jira_repo = JiraRepository()
