import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.coverage import CoverageMatrix, CoverageSummary, MissingMerge
from app.services.folder_coverage import FolderCoverageService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[CoverageSummary])
async def get_coverage_summary(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve aggregate statistics representing repository-wide merge coverages."""
    service = FolderCoverageService()
    result = await service.get_coverage_summary_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/matrix", response_model=ResponseEnvelope[CoverageMatrix])
async def get_coverage_matrix(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch the full Jira x Folder grid matrix mapping release statuses."""
    service = FolderCoverageService()
    result = await service.get_coverage_matrix_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/missing", response_model=ResponseEnvelope[list[MissingMerge]])
async def get_missing_merges(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all expected target folders currently missing release commit updates."""
    service = FolderCoverageService()
    result = await service.get_missing_merges_list(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
