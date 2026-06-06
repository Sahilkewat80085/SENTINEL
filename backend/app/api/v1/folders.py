from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.folder import FolderHealthResult, FolderHealthRank, HeatmapCell
from app.services.folder_health import FolderHealthService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[FolderHealthResult]])
async def get_all_folders_health(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed health scores and metrics for all repository folders."""
    service = FolderHealthService()
    result = await service.compute_all_health(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/ranking", response_model=ResponseEnvelope[List[FolderHealthRank]])
async def get_folder_health_rankings(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch rankings for all repository folders based on their composite health score."""
    service = FolderHealthService()
    result = await service.get_health_ranking(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/heatmap", response_model=ResponseEnvelope[List[HeatmapCell]])
async def get_folder_heatmap_data(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve flat matrix cell list representing metric scores per folder for heatmaps."""
    service = FolderHealthService()
    result = await service.get_heatmap_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/weakest", response_model=ResponseEnvelope[List[FolderHealthResult]])
async def get_weakest_folders(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    limit: int = Query(3, description="Number of weakest folders to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch the N weakest folders in the repository based on health score."""
    service = FolderHealthService()
    result = await service.get_weakest_folders(db, repository_id=repository_id, n=limit)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/{folder}", response_model=ResponseEnvelope[FolderHealthResult])
async def get_folder_health_detail(
    folder: str = Path(..., description="Name of the target folder"),
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed health scores and metrics for a specific folder."""
    service = FolderHealthService()
    result = await service.compute_health(db, repository_id=repository_id, folder=folder)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
