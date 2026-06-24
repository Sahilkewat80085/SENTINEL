import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.snapshot import FolderHealthSnapshot, GovernanceSnapshot


class SnapshotRepository:
    """Repository handling database operations for daily snapshots and historical trends."""

    async def upsert_governance_snapshot(
        self, db: AsyncSession, repository_id: uuid.UUID, snapshot_date: date, data: dict[str, Any]
    ) -> GovernanceSnapshot:
        """Upserts a repository-wide governance snapshot for a specific date."""
        stmt = select(GovernanceSnapshot).where(
            and_(
                GovernanceSnapshot.repository_id == repository_id,
                GovernanceSnapshot.snapshot_date == snapshot_date
            )
        )
        res = await db.execute(stmt)
        snapshot = res.scalar_one_or_none()

        if snapshot:
            # Update
            for key, val in data.items():
                if hasattr(snapshot, key):
                    setattr(snapshot, key, val)
        else:
            # Create
            snapshot = GovernanceSnapshot(
                repository_id=repository_id,
                snapshot_date=snapshot_date,
                **data
            )
            db.add(snapshot)

        await db.flush()
        return snapshot

    async def upsert_folder_health_snapshot(
        self, db: AsyncSession, repository_id: uuid.UUID, snapshot_date: date, folder_name: str, data: dict[str, Any]
    ) -> FolderHealthSnapshot:
        """Upserts an environment/folder specific health snapshot for a specific date."""
        stmt = select(FolderHealthSnapshot).where(
            and_(
                FolderHealthSnapshot.repository_id == repository_id,
                FolderHealthSnapshot.snapshot_date == snapshot_date,
                FolderHealthSnapshot.folder_name == folder_name
            )
        )
        res = await db.execute(stmt)
        snapshot = res.scalar_one_or_none()

        if snapshot:
            # Update
            for key, val in data.items():
                if hasattr(snapshot, key):
                    setattr(snapshot, key, val)
        else:
            # Create
            snapshot = FolderHealthSnapshot(
                repository_id=repository_id,
                snapshot_date=snapshot_date,
                folder_name=folder_name,
                **data
            )
            db.add(snapshot)

        await db.flush()
        return snapshot

    async def get_governance_snapshots(
        self, db: AsyncSession, repository_id: uuid.UUID, days: int = 30
    ) -> list[GovernanceSnapshot]:
        """Fetch repository daily snapshots sorted chronologically."""
        start_date = date.today() - timedelta(days=days)
        stmt = (
            select(GovernanceSnapshot)
            .where(
                and_(
                    GovernanceSnapshot.repository_id == repository_id,
                    GovernanceSnapshot.snapshot_date >= start_date
                )
            )
            .order_by(GovernanceSnapshot.snapshot_date.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_folder_health_snapshots(
        self, db: AsyncSession, repository_id: uuid.UUID, folder_name: str | None = None, days: int = 30
    ) -> list[FolderHealthSnapshot]:
        """Fetch folder health snapshots sorted chronologically."""
        start_date = date.today() - timedelta(days=days)
        filters = [
            FolderHealthSnapshot.repository_id == repository_id,
            FolderHealthSnapshot.snapshot_date >= start_date
        ]
        if folder_name:
            filters.append(FolderHealthSnapshot.folder_name == folder_name)

        stmt = (
            select(FolderHealthSnapshot)
            .where(and_(*filters))
            .order_by(FolderHealthSnapshot.snapshot_date.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


# Singleton instance
snapshot_repo = SnapshotRepository()
