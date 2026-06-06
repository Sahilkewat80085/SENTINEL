import datetime as dt
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TrendPoint(BaseModel):
    """Generic representation of a single metrics metric tracked over time."""

    model_config = ConfigDict(from_attributes=True)

    date: dt.date = Field(..., description="Date of the snapshot metric")
    value: float = Field(..., description="Numerical value of the metric")


class FolderTrendPoint(BaseModel):
    """Folder-specific health metrics captured on a specific day."""

    model_config = ConfigDict(from_attributes=True)

    date: dt.date
    folder_name: str
    health_score: float
    coverage_score: float
    consistency_score: float
    timeliness_score: float
    completeness_score: float


class ViolationTrendPoint(BaseModel):
    """Aggregated governance violations tracked over time."""

    model_config = ConfigDict(from_attributes=True)

    date: dt.date
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_count: int
