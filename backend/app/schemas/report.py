import os
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_serializer


class ReportBase(BaseModel):
    repository_id: uuid.UUID
    report_type: str  # EXCEL or PDF
    config: dict[str, Any] = Field(default_factory=dict)


class ReportCreate(ReportBase):
    file_path: str
    file_size: int | None = None
    generated_by: str | None = None
    expires_at: datetime | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    report_type: str
    file_path: str
    file_size: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    generated_by: str | None = None
    generated_at: datetime
    expires_at: datetime | None = None

    # Frontend compatibility fields
    status: str = "COMPLETE"
    filename: str | None = None
    file_size_bytes: int | None = None
    created_at: datetime

    @model_serializer(mode="wrap")
    def serialize_report(self, handler) -> dict[str, Any]:
        """Custom serialization to ensure frontend-compatible fields are populated."""
        data = handler(self)

        # Populate frontend compatibility fields if not already set
        if not data.get("filename") and self.file_path:
            data["filename"] = os.path.basename(self.file_path)

        if data.get("file_size_bytes") is None:
            data["file_size_bytes"] = self.file_size or 0

        if not data.get("created_at"):
            data["created_at"] = self.generated_at

        # Convert report_type to uppercase (EXCEL, PDF)
        if data.get("report_type"):
            data["report_type"] = data["report_type"].upper()

        return data
