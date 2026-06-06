from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.content import DriftReport
from app.services.content_verification import ContentVerificationService

router = APIRouter()


@router.get("/verification", response_model=ResponseEnvelope[Dict[str, Any]])
async def get_verification_summary(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve statistics comparing identical vs. drifted configurations across target environments."""
    service = ContentVerificationService()
    result = await service.get_verification_summary_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/drift", response_model=ResponseEnvelope[DriftReport])
async def get_drift_report(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch complete content drift reports detailing mismatched files and values."""
    service = ContentVerificationService()
    result = await service.get_drift_report_data(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.post("/verify", response_model=ResponseEnvelope[Dict[str, Any]])
async def trigger_content_verification(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger manual SHA256 scan on repository configurations to identify content drifts."""
    service = ContentVerificationService()
    result = await service.verify_repository_files(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
