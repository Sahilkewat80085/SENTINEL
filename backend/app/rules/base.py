from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel

from app.schemas.coverage import CoverageMatrix
from app.schemas.content import DriftReport
from app.schemas.delay import DelayResult
from app.schemas.folder import FolderHealthResult


class RuleContext(BaseModel):
    """Context container holding all pre-calculated metrics and details for governance analysis."""

    repository_id: uuid.UUID
    repo: Any  # Repository model
    coverage_matrix: CoverageMatrix
    drift_report: DriftReport
    delays: List[DelayResult]
    folder_health: List[FolderHealthResult]
    jira_summaries: List[Dict[str, Any]]
    previous_health: Dict[str, float]

    model_config = {"arbitrary_types_allowed": True}


class RuleViolationInfo(BaseModel):
    """Intermediary data structure representing a detected governance violation before database persistence."""

    rule_id: str
    severity: str
    category: str
    jira_id: Optional[str] = None
    folder_name: Optional[str] = None
    file_path: Optional[str] = None
    description: str
    details: Dict[str, Any] = {}
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
    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        """Evaluates the rule constraints against context. Returns list of violations."""
        pass
