import asyncio
from typing import Any, Dict, List
from sqlalchemy import select
import uuid

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.core.logging import logger
from app.repositories import repository_repo
from app.services.trend_analytics import TrendAnalyticsService


@celery_app.task(name="tasks.capture_daily_snapshot")
def capture_daily_snapshot_task(repository_id: str) -> Dict[str, Any]:
    """Background task to sync and record daily snapshots for a specific repository."""
    logger.info("Executing background daily snapshot capture task for repository", repo_id=repository_id)

    async def _run() -> Dict[str, Any]:
        async with get_db_context() as db:
            service = TrendAnalyticsService()
            repo_uuid = uuid.UUID(repository_id)
            result = await service.capture_daily_snapshot(db, repo_uuid)
            if result.is_failure:
                logger.error("Snapshot capture background task failed", repo_id=repository_id, error=str(result.error))
                raise Exception(result.error.message)
            
            logger.info("Snapshot capture background task completed successfully", repo_id=repository_id)
            return {"repository_id": repository_id, "status": "success", "date": str(result.value.get("date"))}

    return asyncio.run(_run())


@celery_app.task(name="tasks.capture_all_active_snapshots")
def capture_all_active_snapshots_task() -> List[Dict[str, Any]]:
    """Scheduled task to execute daily snapshot captures for all active repositories."""
    logger.info("Starting batch snapshot capturing for all active repositories")

    async def _run() -> List[Dict[str, Any]]:
        async with get_db_context() as db:
            query = select(repository_repo.model).where(repository_repo.model.is_active == True)
            res = await db.execute(query)
            active_repos = list(res.scalars().all())

            results = []
            service = TrendAnalyticsService()

            for repo in active_repos:
                logger.info("Capturing snapshot inside batch job", repo_name=repo.name)
                result = await service.capture_daily_snapshot(db, repo.id)
                results.append({
                    "repository_id": str(repo.id),
                    "repository_name": repo.name,
                    "success": result.is_success,
                    "details": {"date": str(result.value.get("date"))} if result.is_success else str(result.error)
                })

            return results

    return asyncio.run(_run())
