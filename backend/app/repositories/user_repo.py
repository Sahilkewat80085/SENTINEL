
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository class handling query interfaces for authentication and administration of users."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Fetch a user record by username."""
        stmt = select(self.model).where(self.model.username == username)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Fetch a user record by email."""
        stmt = select(self.model).where(self.model.email == email)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


# Singleton instance
user_repo = UserRepository()
