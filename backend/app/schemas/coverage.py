from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class FolderCoverageDetail(BaseModel):
    """Status details for a specific folder release target."""

    folder_name: str
    is_merged: bool
    merge_date: Optional[datetime] = None


class JiraCoverageRow(BaseModel):
    """A row in the coverage matrix representing a single Jira's status across all target folders."""

    jira_id: str
    folders: List[FolderCoverageDetail]
    coverage_pct: float
    status: str = Field(..., description="MERGED | PARTIAL | MISSING")


class CoverageMatrix(BaseModel):
    """Matrix structure containing all rows and headers representing Jira-to-Folder mappings."""

    model_config = ConfigDict(from_attributes=True)

    repository_id: uuid.UUID
    folders_list: List[str] = Field(..., description="List of folders acting as column headers")
    rows: List[JiraCoverageRow]


class CoverageSummary(BaseModel):
    """Aggregate statistics representing repository-wide merge coverages."""

    total_jiras: int
    merged_count: int
    partial_count: int
    missing_count: int
    overall_coverage_pct: float


class MissingMerge(BaseModel):
    """Represents a target folder that is missing updates for a committed Jira."""

    jira_id: str
    folder: str
    last_updated: datetime
