import asyncio
from typing import Any, Dict, List
from sqlalchemy import select

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.core.logging import logger
from app.repositories import repository_repo
from app.services.commit_collector import CommitCollectorService


@celery_app.task(name="tasks.sync_repository")
def sync_repository_task(repository_id: str) -> Dict[str, Any]:
    """Background task to sync commits for a specific repository by ID."""
    logger.info("Executing background sync task for repository", repo_id=repository_id)

    async def _run() -> Dict[str, Any]:
        async with get_db_context() as db:
            service = CommitCollectorService()
            result = await service.sync_repository(db, repository_id)
            if result.is_failure:
                logger.error("Sync background task failed", repo_id=repository_id, error=str(result.error))
                raise Exception(result.error.message)
            
            # Post-sync hooks go here in future steps (materialized views, health scoring, rules, etc.)
            logger.info("Sync background task completed successfully", repo_id=repository_id, result=result.value)
            return result.value

    return asyncio.run(_run())


@celery_app.task(name="tasks.sync_all_repositories")
def sync_all_repositories_task() -> List[Dict[str, Any]]:
    """Scheduled task to execute sync on all active repositories in parallel/sequence."""
    logger.info("Starting batch incremental sync task for all active repositories")

    async def _run() -> List[Dict[str, Any]]:
        async with get_db_context() as db:
            query = select(repository_repo.model).where(repository_repo.model.is_active == True)
            res = await db.execute(query)
            active_repos = list(res.scalars().all())

            results = []
            service = CommitCollectorService()

            for repo in active_repos:
                logger.info("Triggering incremental sync inside batch job", repo_name=repo.name)
                result = await service.sync_repository(db, repo.id)
                results.append({
                    "repository_id": str(repo.id),
                    "repository_name": repo.name,
                    "success": result.is_success,
                    "details": result.value if result.is_success else str(result.error)
                })

            return results

    return asyncio.run(_run())
