import asyncio
from typing import Dict, Any
from sqlalchemy import text

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.core.logging import logger


async def _refresh_materialized_views_helper(db) -> None:
    """Helper executing concurrent view refreshes with standard fallback on failures."""
    try:
        logger.info("Refreshing mv_jira_summary concurrently")
        await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_jira_summary"))
        await db.commit()
    except Exception as e:
        logger.warn("Concurrent refresh of mv_jira_summary failed, fallback to standard", error=str(e))
        try:
            await db.execute(text("REFRESH MATERIALIZED VIEW mv_jira_summary"))
            await db.commit()
        except Exception as ex:
            logger.error("Standard refresh of mv_jira_summary failed", error=str(ex))
            await db.rollback()

    try:
        logger.info("Refreshing mv_coverage_matrix concurrently")
        await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_coverage_matrix"))
        await db.commit()
    except Exception as e:
        logger.warn("Concurrent refresh of mv_coverage_matrix failed, fallback to standard", error=str(e))
        try:
            await db.execute(text("REFRESH MATERIALIZED VIEW mv_coverage_matrix"))
            await db.commit()
        except Exception as ex:
            logger.error("Standard refresh of mv_coverage_matrix failed", error=str(ex))
            await db.rollback()


@celery_app.task(name="tasks.refresh_views")
def refresh_views_task(repository_id: str) -> Dict[str, Any]:
    """Background task to refresh all materialized views to update dashboards cache data."""
    logger.info("Executing background task to refresh materialized views", repo_id=repository_id)

    async def _run() -> Dict[str, Any]:
        async with get_db_context() as db:
            await _refresh_materialized_views_helper(db)
            return {"status": "success", "repository_id": repository_id}

    return asyncio.run(_run())
