import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.result import ServiceResult
from app.repositories import repository_repo
from app.schemas.dashboard import GovernanceScoreDetail
from app.services.exception_detection import ExceptionDetectionService
from app.services.folder_health import FolderHealthService


class GovernanceScoreService:
    """Service to compute overall repository composite governance scores (0-100) and letter grades (A-F)."""

    def __init__(
        self,
        health_service: FolderHealthService | None = None,
        violation_service: ExceptionDetectionService | None = None,
    ) -> None:
        self.health_service = health_service or FolderHealthService()
        self.violation_service = violation_service or ExceptionDetectionService()

    def _determine_grade(self, score: float) -> str:
        """Helper to assign a letter grade based on numeric score thresholds."""
        if score >= 90.0:
            return "A"
        elif score >= 80.0:
            return "B"
        elif score >= 70.0:
            return "C"
        elif score >= 60.0:
            return "D"
        elif score >= 50.0:
            return "E"
        else:
            return "F"

    async def compute_repository_score(
        self, db: AsyncSession, repository_id: uuid.UUID
    ) -> ServiceResult[GovernanceScoreDetail]:
        """Calculates the composite governance score by averaging folder health and subtracting violation penalties."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        # 1. Fetch folder health details
        health_res = await self.health_service.compute_all_health(db, repository_id)
        if health_res.is_failure:
            return ServiceResult.failure(health_res.error)
        folder_health = health_res.value

        # Calculate average health score of environments
        if folder_health:
            folder_health_avg = sum(f.health_score for f in folder_health) / len(folder_health)
        else:
            folder_health_avg = 100.0

        # 2. Fetch active, unacknowledged violations
        violation_sum_res = await self.violation_service.get_violation_summary(db, repository_id)
        if violation_sum_res.is_failure:
            return ServiceResult.failure(violation_sum_res.error)
        summary = violation_sum_res.value

        # Query all active unacknowledged violations to apply penalties
        violations_res = await self.violation_service.get_violations(
            db, repository_id=repository_id, is_acknowledged=False, is_resolved=False
        )
        violations = violations_res.value

        # Calculate penalties:
        # Critical = -5.0 points
        # High = -3.0 points
        # Medium = -1.0 point
        # Low = -0.5 points
        # Maximum penalty is capped at 50 points to prevent extreme swings
        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        high_count = sum(1 for v in violations if v.severity == "HIGH")
        medium_count = sum(1 for v in violations if v.severity == "MEDIUM")
        low_count = sum(1 for v in violations if v.severity == "LOW")

        penalty = (
            (critical_count * 5.0) +
            (high_count * 3.0) +
            (medium_count * 1.0) +
            (low_count * 0.5)
        )
        penalty = min(penalty, 50.0)

        # Final composite score calculation
        score = max(0.0, folder_health_avg - penalty)
        score = round(score, 2)
        grade = self._determine_grade(score)

        detail = GovernanceScoreDetail(
            score=score,
            grade=grade,
            folder_health_average=round(folder_health_avg, 2),
            violation_penalty=round(penalty, 2),
            active_critical_count=critical_count,
            active_high_count=high_count,
            active_medium_count=medium_count,
            active_low_count=low_count
        )

        return ServiceResult.success(detail)
