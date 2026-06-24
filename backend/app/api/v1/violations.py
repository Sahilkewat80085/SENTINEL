import uuid
from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.violation import (
    RuleViolationResponse,
    ViolationAcknowledgeRequest,
    ViolationSummary,
)
from app.services.exception_detection import ExceptionDetectionService

router = APIRouter()


@router.post("/evaluate", response_model=ResponseEnvelope[list[RuleViolationResponse]])
async def evaluate_repository_violations(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger a full evaluation of all governance rules and update the violation state."""
    service = ExceptionDetectionService()
    result = await service.evaluate_rules(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("", response_model=ResponseEnvelope[list[RuleViolationResponse]])
async def get_repository_violations(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    severity: str | None = Query(None, description="Filter by severity: CRITICAL | HIGH | MEDIUM | LOW"),
    category: str | None = Query(None, description="Filter by category: COVERAGE | DELAY | CONSISTENCY | PROPAGATION"),
    is_acknowledged: bool | None = Query(None, description="Filter by acknowledgement status"),
    is_resolved: bool | None = Query(None, description="Filter by resolution status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch list of governance violations for a repository matching filtered criteria."""
    service = ExceptionDetectionService()
    result = await service.get_violations(
        db,
        repository_id=repository_id,
        severity=severity,
        category=category,
        is_acknowledged=is_acknowledged,
        is_resolved=is_resolved
    )
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.get("/summary", response_model=ResponseEnvelope[ViolationSummary])
async def get_violation_summary(
    repository_id: uuid.UUID = Query(..., description="Context repository UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch aggregate KPIs representing the overall violation state of the repository."""
    service = ExceptionDetectionService()
    result = await service.get_violation_summary(db, repository_id=repository_id)
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)


@router.post("/{violation_id}/acknowledge", response_model=ResponseEnvelope[RuleViolationResponse])
async def acknowledge_violation(
    req: ViolationAcknowledgeRequest,
    violation_id: uuid.UUID = Path(..., description="UUID of the rule violation to acknowledge"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Acknowledge an active violation with developer note and justification comments."""
    service = ExceptionDetectionService()
    result = await service.acknowledge_violation(
        db,
        violation_id=violation_id,
        username=current_user.username,
        note=req.acknowledge_note
    )
    if result.is_failure:
        raise result.error
    return ResponseEnvelope(success=True, data=result.value)
