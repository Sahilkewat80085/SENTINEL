import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.core.logging import logger
from app.models.repository import Repository
from app.models.user import User
from app.repositories import repository_repo
from app.schemas.common import ResponseEnvelope
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from app.services.commit_collector import CommitCollectorService
from app.tasks.ingestion import sync_repository_task

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[list[RepositoryResponse]])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all registered repository configurations."""
    repos = await repository_repo.get_multi(db)
    return ResponseEnvelope(success=True, data=repos)


@router.post(
    "",
    response_model=ResponseEnvelope[RepositoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_repository(
    repo_in: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Register a new repository configuration for auditing."""
    # Check duplicate names
    stmt = select(Repository).where(Repository.name == repo_in.name)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ValidationException(
            message=f"Repository configuration with name '{repo_in.name}' already exists."
        )

    # Insert configuration
    db_obj = await repository_repo.create(db, obj_in=repo_in.model_dump())
    await db.commit()
    await db.refresh(db_obj)

    return ResponseEnvelope(success=True, data=db_obj)


@router.get("/{id}", response_model=ResponseEnvelope[RepositoryResponse])
async def get_repository(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch repository configuration details by UUID."""
    repo = await repository_repo.get(db, id=id)
    if not repo:
        raise EntityNotFoundException("Repository", id)
    return ResponseEnvelope(success=True, data=repo)


@router.put("/{id}", response_model=ResponseEnvelope[RepositoryResponse])
async def update_repository(
    id: uuid.UUID,
    repo_in: RepositoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update configurations of a registered repository."""
    repo = await repository_repo.get(db, id=id)
    if not repo:
        raise EntityNotFoundException("Repository", id)

    updated_repo = await repository_repo.update(db, db_obj=repo, obj_in=repo_in)
    await db.commit()
    await db.refresh(updated_repo)

    return ResponseEnvelope(success=True, data=updated_repo)


@router.delete("/{id}", response_model=ResponseEnvelope[dict[str, Any]])
async def delete_repository(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete a registered repository and its associated commit records."""
    repo = await repository_repo.get(db, id=id)
    if not repo:
        raise EntityNotFoundException("Repository", id)

    await repository_repo.remove(db, id=id)
    await db.commit()

    return ResponseEnvelope(
        success=True,
        data={"message": f"Repository '{repo.name}' and all audits deleted successfully."},
    )


@router.post("/{id}/sync", response_model=ResponseEnvelope[dict[str, Any]])
async def sync_repository(
    id: uuid.UUID,
    background: bool = Query(
        default=True,
        description="True triggers Celery task; False runs synchronously for testing/direct calls",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Initiates a synchronization sync on the repository to fetch new commits."""
    repo = await repository_repo.get(db, id=id)
    if not repo:
        raise EntityNotFoundException("Repository", id)

    if background:
        # Trigger Celery background task
        task = sync_repository_task.delay(str(id))
        logger.info("Triggered database sync in Celery background task", repo_name=repo.name, task_id=task.id)
        return ResponseEnvelope(
            success=True,
            data={
                "message": "Synchronization task sent to background queue successfully.",
                "task_id": task.id,
                "status": "pending",
            },
        )
    else:
        # Run service synchronously
        logger.info("Triggering database sync synchronously", repo_name=repo.name)
        service = CommitCollectorService()
        result = await service.sync_repository(db, repository_id=id)
        if result.is_failure:
            raise result.error

        return ResponseEnvelope(success=True, data=result.value)
