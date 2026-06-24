
from pydantic import BaseModel, ConfigDict, Field


class ContentVerificationResult(BaseModel):
    """Result structure verifying identical or drifted file contents across target folders."""

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    status: str = Field(..., description="IDENTICAL | DIFFERENT | MISSING")
    drift_score: float = Field(..., description="Divergence score from 0.0 to 1.0")
    folder_hashes: dict[str, str] = Field(..., description="Mapping of folder names to their file hash")
    majority_hash: str | None = None
    divergent_folders: list[str] = Field(default_factory=list, description="Folders with mismatched hashes")
    file_sizes: dict[str, int] = Field(default_factory=dict, description="File size mappings in bytes")


class DriftReport(BaseModel):
    """Aggregate report containing all configuration file drifts."""

    drifted_files: list[ContentVerificationResult]
    overall_drift_score: float
