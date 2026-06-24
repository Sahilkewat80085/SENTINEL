from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.audit_repo import audit_repo
from app.repositories.user_repo import user_repo
from app.schemas.auth import Token, UserResponse
from app.schemas.common import ResponseEnvelope

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """OAuth2 compatible token login, returning a JWT access token."""
    user = await user_repo.get_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        # Log failed login attempt
        await audit_repo.log_action(
            db,
            action="login_failed",
            entity_type="users",
            entity_id=form_data.username,
            details={"reason": "Invalid credentials"},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user profile",
        )

    # Log successful login
    await audit_repo.log_action(
        db,
        user_id=user.id,
        action="login_success",
        entity_type="users",
        entity_id=str(user.id),
    )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()

    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve profile details for the currently authenticated user."""
    return ResponseEnvelope(success=True, data=current_user)
