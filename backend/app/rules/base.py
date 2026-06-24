import uuid
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.schemas.content import DriftReport
from app.schemas.coverage import CoverageMatrix
from app.schemas.delay import DelayResult
from app.schemas.folder import FolderHealthResult


class RuleContext(BaseModel):
    """Context container holding all pre-calculated metrics and details for governance analysis."""

    repository_id: uuid.UUID
    repo: Any  # Repository model
    coverage_matrix: CoverageMatrix
    drift_report: DriftReport
    delays: list[DelayResult]
    folder_health: list[FolderHealthResult]
    jira_summaries: list[dict[str, Any]]
    previous_health: dict[str, float]

    model_config = {"arbitrary_types_allowed": True}


class RuleViolationInfo(BaseModel):
    """Intermediary data structure representing a detected governance violation before database persistence."""

    rule_id: str
    severity: str
    category: str
    jira_id: str | None = None
    folder_name: str | None = None
    file_path: str | None = None
    description: str
    details: dict[str, Any] = {}
    is_acknowledged: bool = False


class GovernanceRule(ABC):
    """Abstract base class for all pluggable governance rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique ID of the rule, e.g., 'GOV-001'."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the rule."""
        pass

    @property
    @abstractmethod
    def severity(self) -> str:
        """Default severity band: CRITICAL | HIGH | MEDIUM | LOW | INFO."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Category band: COVERAGE | DELAY | CONSISTENCY | PROPAGATION."""
        pass

    @abstractmethod
    def evaluate(self, context: RuleContext) -> list[RuleViolationInfo]:
        """Evaluates the rule constraints against context. Returns list of violations."""
        pass
