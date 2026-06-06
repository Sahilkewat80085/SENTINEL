import asyncio
import uuid
from typing import Dict, Any

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.core.logging import logger
from app.services.content_verification import ContentVerificationService
from app.services.exception_detection import ExceptionDetectionService


@celery_app.task(name="tasks.verify_files")
def verify_files_task(repository_id: str) -> Dict[str, Any]:
    """Background task to run content verification scanner for a repository."""
    logger.info("Executing background files verification task for repository", repo_id=repository_id)

    async def _run() -> Dict[str, Any]:
        async with get_db_context() as db:
            service = ContentVerificationService()
            repo_uuid = uuid.UUID(repository_id)
            result = await service.verify_repository_files(db, repo_uuid)
            if result.is_failure:
                logger.error("Content verification failed", repo_id=repository_id, error=str(result.error))
                raise Exception(result.error.message)
            
            logger.info("Content verification completed successfully", repo_id=repository_id)
            return result.value

    return asyncio.run(_run())


@celery_app.task(name="tasks.evaluate_rules")
def evaluate_rules_task(repository_id: str) -> Dict[str, Any]:
    """Background task to evaluate repository governance rules."""
    logger.info("Executing background rule evaluation task for repository", repo_id=repository_id)

    async def _run() -> Dict[str, Any]:
        async with get_db_context() as db:
            service = ExceptionDetectionService()
            repo_uuid = uuid.UUID(repository_id)
            result = await service.evaluate_rules(db, repo_uuid)
            if result.is_failure:
                logger.error("Rule evaluation failed", repo_id=repository_id, error=str(result.error))
                raise Exception(result.error.message)
            
            logger.info("Rule evaluation completed successfully", repo_id=repository_id, violations_count=len(result.value))
            return {"status": "success", "violations_count": len(result.value)}

    return asyncio.run(_run())
