from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "sentinel_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Optional configuration settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto-discover tasks from the tasks package (Step 3 onwards)
    imports=["app.tasks"] if hasattr(settings, "TASKS") else [],
    # Task time limits
    task_time_limit=1800,  # 30 minutes max execution time
    task_soft_time_limit=1500,
)

# For debugging / celery CLI convenience
if __name__ == "__main__":
    celery_app.start()
