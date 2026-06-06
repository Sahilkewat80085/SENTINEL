from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class MetaData(BaseModel):
    """Standard pagination/runtime metadata block returned in APIs."""

    total: int
    page: int
    page_size: int
    has_next: bool
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response wrapper envelope matching system architecture specifications."""

    success: bool
    data: Optional[T] = None
    meta: Optional[MetaData] = None
    errors: Optional[List[Dict[str, Any]]] = None  # Wait, dict type needs to import Dict or use dict


class ErrorDetail(BaseModel):
    """Specific validation/runtime error detail item."""

    code: str
    field: Optional[str] = None
    message: str


class ErrorResponseEnvelope(BaseModel):
    """Standard API error response schema envelope matching design specifications."""

    success: bool = False
    data: None = None
    meta: None = None
    errors: List[ErrorDetail]


# Common query parameter schemas
class PaginationParams(BaseModel):
    """Basic pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class DateRangeParams(BaseModel):
    """Basic date filtering criteria."""

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
