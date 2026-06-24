from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async CRUD repository base class."""

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Fetch a single record by its primary key ID."""
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Fetch multiple records with offset pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any]) -> ModelType:
        """Create and persist a new model instance."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: dict[str, Any] | Any,
    ) -> ModelType:
        """Update fields on an existing model instance."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> ModelType | None:
        """Delete a record by its primary key ID."""
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj
