from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Access token exchange payload returned after authentication."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Subject data contained inside standard JWT token payloads."""

    sub: Optional[str] = None


class UserLogin(BaseModel):
    """User authentication payload representing login credentials."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Detailed user response serialization payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
