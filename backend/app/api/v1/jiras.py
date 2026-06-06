from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.common import MetaData, ResponseEnvelope
from app.schemas.jira import JiraDetail, JiraSummary
from app.services.jira_aggregation import JiraAggregationService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[JiraSummary]])
async def list_jiras(
    repository_id: Optional[uuid.UUID] = Query(None, description="Filter by repository UUID"),
    search: Optional[str] = Query(None, description="Search by Jira ID key"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve paginated summaries of Jira issues detected in commits."""
    skip = (page - 1) * page_size
    service = JiraAggregationService()
    
    result = await service.get_jira_list(
        db, repository_id=repository_id, search=search, skip=skip, limit=page_size
    )
    if result.is_failure:
        raise result.error

    summaries, total = result.value
    has_next = total > (page * page_size)

    meta = MetaData(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next
    )

    return ResponseEnvelope(success=True, data=summaries, meta=meta)


@router.get("/{jira_id}", response_model=ResponseEnvelope[JiraDetail])
async def get_jira(
    jira_id: str,
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch complete ticket details and merge progress timeline by Jira key."""
    service = JiraAggregationService()
    result = await service.get_jira_detail(db, jira_id=jira_id, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
