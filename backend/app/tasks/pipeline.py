from celery import chain

from app.celery_app import celery_app
from app.core.logging import logger
from app.tasks.analysis import evaluate_rules_task, verify_files_task
from app.tasks.maintenance import refresh_views_task
from app.tasks.snapshots import capture_daily_snapshot_task


@celery_app.task(name="tasks.trigger_repository_analysis")
def trigger_repository_analysis_task(repository_id: str) -> None:
    """Orchestrates post-sync governance pipeline tasks sequentially using a Celery chain."""
    logger.info("Scheduling post-sync analysis pipeline chain", repo_id=repository_id)

    # Celery Chain sequence:
    # 1. Refresh materialized views to update aggregates.
    # 2. Perform file content hashing and check drifts.
    # 3. Evaluate governance rule exceptions.
    # 4. Capture daily metrics snapshot.
    pipeline = chain(
        refresh_views_task.si(repository_id),
        verify_files_task.si(repository_id),
        evaluate_rules_task.si(repository_id),
        capture_daily_snapshot_task.si(repository_id)
    )
    pipeline.delay()
