from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User


async def get_current_user() -> User:
    """Dependency helper to resolve the currently authenticated User.

    Temporarily returns a mock system admin user during development
    until Step 11 authentication is fully wired in.
    """
    # Return a mock admin user for testing API routes before full security setup
    import uuid

    return User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@sentinel.local",
        role="admin",
        is_active=True,
    )
