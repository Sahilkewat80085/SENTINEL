from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional


class FolderHealthResult(BaseModel):
    """Detailed health evaluation metrics for a single folder."""

    model_config = ConfigDict(from_attributes=True)

    folder_name: str = Field(..., description="Name of the folder")
    coverage_score: float = Field(..., description="Coverage score: percentage of Jiras merged in this folder (35% weight)")
    consistency_score: float = Field(..., description="Consistency score: percentage of identical files (30% weight)")
    timeliness_score: float = Field(..., description="Timeliness score: propagation delay score (20% weight)")
    completeness_score: float = Field(..., description="Completeness score: percentage of expected files present (15% weight)")
    health_score: float = Field(..., description="Weighted composite health score (0-100)")
    classification: str = Field(..., description="Health classification: EXCELLENT | GOOD | WARNING | POOR | CRITICAL")


class FolderHealthRank(BaseModel):
    """Ranking details for a folder based on its health score."""

    model_config = ConfigDict(from_attributes=True)

    folder_name: str
    health_score: float
    classification: str
    rank: int


class HeatmapCell(BaseModel):
    """Flat representation of folder metric score for heatmaps."""

    model_config = ConfigDict(from_attributes=True)

    folder_name: str
    metric: str  # 'coverage' | 'consistency' | 'timeliness' | 'completeness' | 'health'
    score: float
