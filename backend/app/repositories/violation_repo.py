from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.violation import RuleViolation
from app.repositories.base import BaseRepository


class ViolationRepository(BaseRepository[RuleViolation]):
    """Repository class for rule violations handling custom filters and bulk operations."""

    def __init__(self) -> None:
        super().__init__(RuleViolation)

    async def get_active_for_repository(self, db: AsyncSession, repository_id: uuid.UUID) -> List[RuleViolation]:
        """Fetch all active (unresolved) violations for a given repository."""
        stmt = select(self.model).where(
            and_(
                self.model.repository_id == repository_id,
                self.model.resolved_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_all_for_repository(
        self,
        db: AsyncSession,
        repository_id: uuid.UUID,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        is_acknowledged: Optional[bool] = None,
        is_resolved: Optional[bool] = None,
    ) -> List[RuleViolation]:
        """Fetch violations with custom query filters for dashboard list views."""
        filters = [self.model.repository_id == repository_id]

        if severity:
            filters.append(self.model.severity == severity)
        if category:
            filters.append(self.model.category == category)
        if is_acknowledged is not None:
            filters.append(self.model.is_acknowledged == is_acknowledged)
        if is_resolved is not None:
            if is_resolved:
                filters.append(self.model.resolved_at.is_not(None))
            else:
                filters.append(self.model.resolved_at.is_(None))

        stmt = select(self.model).where(and_(*filters)).order_by(self.model.detected_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())


# Singleton instance
violation_repo = ViolationRepository()
