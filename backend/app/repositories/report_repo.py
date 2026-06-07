from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository class for Report database operations."""

    async def get_by_repository(
        self, db: AsyncSession, repository_id: uuid.UUID, *, skip: int = 0, limit: int = 100
    ) -> List[Report]:
        """Fetch all reports for a specific repository, ordered by generation date desc."""
        query = (
            select(self.model)
            .where(self.model.repository_id == repository_id)
            .order_by(self.model.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


report_repo = ReportRepository(Report)
