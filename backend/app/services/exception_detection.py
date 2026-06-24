import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.core.result import ServiceResult
from app.models.snapshot import FolderHealthSnapshot
from app.models.violation import RuleViolation
from app.repositories import repository_repo
from app.repositories.violation_repo import violation_repo
from app.rules.base import RuleContext, RuleViolationInfo
from app.rules.registry import get_registered_rules
from app.schemas.violation import ViolationSummary
from app.services.content_verification import ContentVerificationService
from app.services.folder_coverage import FolderCoverageService
from app.services.folder_health import FolderHealthService
from app.services.merge_delay import MergeDelayService


class ExceptionDetectionService:
    """Service to evaluate governance rules, manage active violations, and handle developer acknowledgements."""

    def __init__(
        self,
        coverage_service: FolderCoverageService | None = None,
        content_service: ContentVerificationService | None = None,
        delay_service: MergeDelayService | None = None,
        health_service: FolderHealthService | None = None,
    ) -> None:
        self.coverage_service = coverage_service or FolderCoverageService()
        self.content_service = content_service or ContentVerificationService()
        self.delay_service = delay_service or MergeDelayService()
        self.health_service = health_service or FolderHealthService()

    async def evaluate_rules(
        self, db: AsyncSession, repository_id: uuid.UUID
    ) -> ServiceResult[list[RuleViolation]]:
        """Orchestrates full rule evaluations and updates database violations state (soft-resolving cleared items)."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        logger.info("Starting governance rule evaluations", repo_name=repo.name)

        # 1. Gather coverage matrix
        cov_matrix_res = await self.coverage_service.get_coverage_matrix_data(db, repository_id)
        if cov_matrix_res.is_failure:
            return ServiceResult.failure(cov_matrix_res.error)
        coverage_matrix = cov_matrix_res.value

        # 2. Gather content drift report
        drift_res = await self.content_service.get_drift_report_data(db, repository_id)
        if drift_res.is_failure:
            return ServiceResult.failure(drift_res.error)
        drift_report = drift_res.value

        # 3. Gather delay results
        delays_res = await self.delay_service.get_repository_delays(db, repository_id)
        if delays_res.is_failure:
            return ServiceResult.failure(delays_res.error)
        delays = delays_res.value

        # 4. Gather folder health results
        health_res = await self.health_service.compute_all_health(db, repository_id)
        if health_res.is_failure:
            return ServiceResult.failure(health_res.error)
        folder_health = health_res.value

        # 5. Gather Jira aggregate details
        stmt_jiras = text("""
            SELECT jira_id, commit_count AS commits_count, author_count AS authors_count, last_updated 
            FROM mv_jira_summary 
            WHERE repository_id = :repo_id
        """)
        jira_res = await db.execute(stmt_jiras, {"repo_id": repository_id})
        jira_summaries = []
        for r in jira_res.all():
            jira_summaries.append({
                "jira_id": r.jira_id,
                "commits_count": r.commits_count,
                "authors_count": r.authors_count,
                "last_updated": r.last_updated
            })

        # 6. Gather previous health snapshots
        stmt_latest_date = (
            select(FolderHealthSnapshot.snapshot_date)
            .where(FolderHealthSnapshot.repository_id == repository_id)
            .order_by(FolderHealthSnapshot.snapshot_date.desc())
            .limit(1)
        )
        date_res = await db.execute(stmt_latest_date)
        latest_date = date_res.scalar_one_or_none()

        previous_health = {}
        if latest_date:
            stmt_prev_scores = (
                select(FolderHealthSnapshot.folder_name, FolderHealthSnapshot.health_score)
                .where(
                    FolderHealthSnapshot.repository_id == repository_id,
                    FolderHealthSnapshot.snapshot_date == latest_date
                )
            )
            prev_res = await db.execute(stmt_prev_scores)
            previous_health = {row[0]: float(row[1]) for row in prev_res.all() if row[1] is not None}

        # 7. Construct RuleContext
        context = RuleContext(
            repository_id=repository_id,
            repo=repo,
            coverage_matrix=coverage_matrix,
            drift_report=drift_report,
            delays=delays,
            folder_health=folder_health,
            jira_summaries=jira_summaries,
            previous_health=previous_health
        )

        # 8. Evaluate all registered rules
        detected_violations: list[RuleViolationInfo] = []
        rules = get_registered_rules()
        for rule in rules:
            try:
                rule_violations = rule.evaluate(context)
                detected_violations.extend(rule_violations)
            except Exception as e:
                logger.error("Error evaluating governance rule", rule_id=rule.rule_id, error=str(e))

        # 9. Sync with Database
        # Fetch existing active violations from DB
        existing_active = await violation_repo.get_active_for_repository(db, repository_id)

        # Build lookup table for existing active violations
        # Key: (rule_id, jira_id, folder_name, file_path)
        existing_lookup = {}
        for ev in existing_active:
            key = (ev.rule_id, ev.jira_id, ev.folder_name, ev.file_path)
            existing_lookup[key] = ev

        processed_ids = set()
        active_violations_to_return = []
        now = datetime.now(timezone.utc)

        # Process newly detected violations
        for dv in detected_violations:
            key = (dv.rule_id, dv.jira_id, dv.folder_name, dv.file_path)

            if key in existing_lookup:
                # Violation is still present, update details/description
                ev = existing_lookup[key]
                ev.description = dv.description
                ev.details = dv.details
                ev.resolved_at = None  # Ensure it remains unresolved
                db.add(ev)
                active_violations_to_return.append(ev)
                processed_ids.add(ev.id)
            else:
                # Create a new violation
                new_violation = RuleViolation(
                    repository_id=repository_id,
                    rule_id=dv.rule_id,
                    severity=dv.severity,
                    category=dv.category,
                    jira_id=dv.jira_id,
                    folder_name=dv.folder_name,
                    file_path=dv.file_path,
                    description=dv.description,
                    details=dv.details,
                    is_acknowledged=False
                )
                db.add(new_violation)
                await db.flush()  # populate ID
                active_violations_to_return.append(new_violation)

        # Resolve active violations in DB that were not detected during this scan
        for ev in existing_active:
            if ev.id not in processed_ids:
                ev.resolved_at = now
                db.add(ev)

        await db.commit()
        logger.info(
            "Rule evaluation sync complete",
            total_active=len(active_violations_to_return),
            newly_resolved=len(existing_active) - len(processed_ids)
        )

        return ServiceResult.success(active_violations_to_return)

    async def get_violations(
        self,
        db: AsyncSession,
        repository_id: uuid.UUID,
        severity: str | None = None,
        category: str | None = None,
        is_acknowledged: bool | None = None,
        is_resolved: bool | None = None,
    ) -> ServiceResult[list[RuleViolation]]:
        """Fetch all violations for a repository matching filtered criteria."""
        violations = await violation_repo.get_all_for_repository(
            db,
            repository_id=repository_id,
            severity=severity,
            category=category,
            is_acknowledged=is_acknowledged,
            is_resolved=is_resolved
        )
        return ServiceResult.success(violations)

    async def acknowledge_violation(
        self,
        db: AsyncSession,
        violation_id: uuid.UUID,
        username: str,
        note: str | None = None
    ) -> ServiceResult[RuleViolation]:
        """Acknowledge an active violation with developer note and timestamp."""
        violation = await violation_repo.get(db, violation_id)
        if not violation:
            return ServiceResult.failure(EntityNotFoundException("RuleViolation", violation_id))

        violation.is_acknowledged = True
        violation.acknowledged_by = username
        violation.acknowledged_at = datetime.now(timezone.utc)
        violation.acknowledge_note = note

        db.add(violation)
        await db.commit()
        await db.refresh(violation)

        logger.info("Rule violation acknowledged", violation_id=violation_id, developer=username)
        return ServiceResult.success(violation)

    async def get_violation_summary(
        self, db: AsyncSession, repository_id: uuid.UUID
    ) -> ServiceResult[ViolationSummary]:
        """Aggregates active violations to build high-level dashboard summaries."""
        repo = await repository_repo.get(db, repository_id)
        if not repo:
            return ServiceResult.failure(EntityNotFoundException("Repository", repository_id))

        # Query all active violations
        active_violations = await violation_repo.get_all_for_repository(
            db, repository_id=repository_id, is_resolved=False
        )

        total_violations = len(active_violations)
        critical_count = sum(1 for v in active_violations if v.severity == "CRITICAL")
        high_count = sum(1 for v in active_violations if v.severity == "HIGH")
        medium_count = sum(1 for v in active_violations if v.severity == "MEDIUM")
        low_count = sum(1 for v in active_violations if v.severity == "LOW")
        acknowledged_count = sum(1 for v in active_violations if v.is_acknowledged)
        unacknowledged_count = total_violations - acknowledged_count

        # Group by category counts
        by_category = {}
        for v in active_violations:
            by_category[v.category] = by_category.get(v.category, 0) + 1

        summary = ViolationSummary(
            total_violations=total_violations,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            acknowledged_count=acknowledged_count,
            unacknowledged_count=unacknowledged_count,
            by_category=by_category
        )

        return ServiceResult.success(summary)
