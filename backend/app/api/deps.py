from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_repo import user_repo

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency helper to resolve the default authenticated User, bypassing JWT checks."""
    user = await user_repo.get_by_username(db, username="admin")
    if user is None:
        user = User(
            username="admin",
            email="admin@sentinel.local",
            role="admin",
            is_active=True
        )
    return user
