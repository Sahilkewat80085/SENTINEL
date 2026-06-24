import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.delay import DelayStatistics, FolderDelayRank
from app.services.merge_delay import MergeDelayService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[DelayStatistics])
async def get_delay_statistics(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve overall propagation delay KPIs and status distributions."""
    service = MergeDelayService()
    result = await service.get_delay_statistics_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/ranking", response_model=ResponseEnvelope[list[FolderDelayRank]])
async def get_folder_delay_rankings(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch environmental delay rankings comparing average propagation speeds."""
    service = MergeDelayService()
    result = await service.get_delay_statistics_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value.folder_rankings)
