from datetime import datetime
from typing import Any, Dict, Optional
import os
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer


class ReportBase(BaseModel):
    repository_id: uuid.UUID
    report_type: str  # EXCEL or PDF
    config: Dict[str, Any] = Field(default_factory=dict)


class ReportCreate(ReportBase):
    file_path: str
    file_size: Optional[int] = None
    generated_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    report_type: str
    file_path: str
    file_size: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    generated_by: Optional[str] = None
    generated_at: datetime
    expires_at: Optional[datetime] = None

    # Frontend compatibility fields
    status: str = "COMPLETE"
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime

    @model_serializer(mode="wrap")
    def serialize_report(self, handler) -> Dict[str, Any]:
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
