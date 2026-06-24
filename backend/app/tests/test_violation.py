import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.repository import Repository
from app.models.violation import RuleViolation
from app.repositories import violation_repo
from app.rules.base import RuleContext
from app.rules.gov_001_vanilla_only import VanillaOnlyRule
from app.rules.gov_002_low_coverage import LowCoverageRule
from app.rules.gov_003_severe_delay import SevereDelayRule
from app.rules.gov_004_content_drift import ContentDriftRule
from app.rules.gov_005_stale_jira import StaleJiraRule
from app.rules.gov_006_single_folder import SingleFolderRule
from app.rules.gov_007_author_isolation import AuthorIsolationRule
from app.rules.gov_008_folder_regression import FolderRegressionRule
from app.rules.gov_009_mass_missing import MassMissingRule
from app.rules.gov_010_zero_propagation import ZeroPropagationRule
from app.schemas.content import ContentVerificationResult, DriftReport
from app.schemas.coverage import CoverageMatrix, FolderCoverageDetail, JiraCoverageRow
from app.schemas.delay import DelayResult
from app.schemas.folder import FolderHealthResult
from app.services.exception_detection import ExceptionDetectionService

REPO_ID = uuid.UUID("8c3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f")


@pytest.fixture
def base_context() -> RuleContext:
    repo = Repository(id=REPO_ID, name="test-repo", folders=["vanilla", "MET", "AMO"])

    coverage_matrix = CoverageMatrix(
        repository_id=REPO_ID,
        folders_list=["vanilla", "MET", "AMO"],
        rows=[
            JiraCoverageRow(
                jira_id="JIRA-1",
                folders=[
                    FolderCoverageDetail(folder_name="vanilla", is_merged=True, merge_date=None),
                    FolderCoverageDetail(folder_name="MET", is_merged=True, merge_date=None),
                    FolderCoverageDetail(folder_name="AMO", is_merged=True, merge_date=None),
                ],
                coverage_pct=100.0,
                status="MERGED"
            )
        ]
    )

    drift_report = DriftReport(drifted_files=[], overall_drift_score=0.0)

    delays = [
        DelayResult(
            jira_id="JIRA-1",
            initial_commit_date=datetime.now(timezone.utc) - timedelta(days=2),
            folder_merge_dates={"vanilla": datetime.now(timezone.utc), "MET": datetime.now(timezone.utc), "AMO": datetime.now(timezone.utc)},
            propagation_delay_days=1.0,
            status="HEALTHY"
        )
    ]

    folder_health = [
        FolderHealthResult(
            folder_name="vanilla", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        ),
        FolderHealthResult(
            folder_name="MET", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        ),
        FolderHealthResult(
            folder_name="AMO", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        )
    ]

    jira_summaries = [
        {
            "jira_id": "JIRA-1",
            "commits_count": 2,
            "authors_count": 2,
            "last_updated": datetime.now(timezone.utc)
        }
    ]

    return RuleContext(
        repository_id=REPO_ID,
        repo=repo,
        coverage_matrix=coverage_matrix,
        drift_report=drift_report,
        delays=delays,
        folder_health=folder_health,
        jira_summaries=jira_summaries,
        previous_health={}
    )


def test_gov_001_vanilla_only(base_context) -> None:
    rule = VanillaOnlyRule()

    # 1. No violations in base context
    assert len(rule.evaluate(base_context)) == 0

    # 2. Trigger violation
    base_context.coverage_matrix.rows[0].folders[0].is_merged = True # vanilla
    base_context.coverage_matrix.rows[0].folders[1].is_merged = False # MET
    base_context.coverage_matrix.rows[0].folders[2].is_merged = False # AMO

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-001"
    assert violations[0].jira_id == "JIRA-1"


def test_gov_002_low_coverage(base_context) -> None:
    rule = LowCoverageRule()
    assert len(rule.evaluate(base_context)) == 0

    # Trigger low coverage (<25%)
    base_context.folder_health[1].coverage_score = 15.0 # MET low coverage
    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-002"
    assert violations[0].folder_name == "MET"


def test_gov_003_severe_delay(base_context) -> None:
    rule = SevereDelayRule()
    assert len(rule.evaluate(base_context)) == 0

    # Trigger severe delay (>30 days)
    base_context.delays[0].propagation_delay_days = 35.0
    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-003"
    assert violations[0].jira_id == "JIRA-1"


def test_gov_004_content_drift(base_context) -> None:
    rule = ContentDriftRule()
    assert len(rule.evaluate(base_context)) == 0

    # Trigger drift
    base_context.drift_report.drifted_files = [
        ContentVerificationResult(
            file_path="configs/settings.yaml",
            status="DIFFERENT",
            drift_score=0.33,
            folder_hashes={"vanilla": "sha1", "MET": "sha1", "AMO": "sha2"},
            majority_hash="sha1",
            divergent_folders=["AMO"],
            file_sizes={"vanilla": 10, "MET": 10, "AMO": 10}
        )
    ]
    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-004"
    assert violations[0].file_path == "configs/settings.yaml"
    assert violations[0].folder_name == "AMO"


def test_gov_005_stale_jira(base_context) -> None:
    rule = StaleJiraRule()
    assert len(rule.evaluate(base_context)) == 0

    # Trigger stale (>60 days inactive)
    base_context.jira_summaries[0]["last_updated"] = datetime.now(timezone.utc) - timedelta(days=65)
    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-005"
    assert violations[0].jira_id == "JIRA-1"


def test_gov_006_single_folder(base_context) -> None:
    rule = SingleFolderRule()
    assert len(rule.evaluate(base_context)) == 0

    # Merged in vanilla and MET, but missing in AMO (only 1 non-vanilla folder)
    base_context.coverage_matrix.rows[0].folders[0].is_merged = True # vanilla
    base_context.coverage_matrix.rows[0].folders[1].is_merged = True # MET
    base_context.coverage_matrix.rows[0].folders[2].is_merged = False # AMO

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-006"
    assert violations[0].jira_id == "JIRA-1"


def test_gov_007_author_isolation(base_context) -> None:
    rule = AuthorIsolationRule()
    assert len(rule.evaluate(base_context)) == 0

    # contributor isolation (1 author, >= 10 commits)
    base_context.jira_summaries[0]["authors_count"] = 1
    base_context.jira_summaries[0]["commits_count"] = 12

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-007"
    assert violations[0].jira_id == "JIRA-1"


def test_gov_008_folder_regression(base_context) -> None:
    rule = FolderRegressionRule()
    assert len(rule.evaluate(base_context)) == 0

    # previous health was 95, current health is 80 (regression of 15 points, threshold 10)
    base_context.previous_health = {"MET": 95.0}
    base_context.folder_health[1].health_score = 80.0

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-008"
    assert violations[0].folder_name == "MET"


def test_gov_009_mass_missing(base_context) -> None:
    rule = MassMissingRule()
    assert len(rule.evaluate(base_context)) == 0

    # Add 5 missing rows in MET
    rows = []
    for i in range(5):
        rows.append(
            JiraCoverageRow(
                jira_id=f"JIRA-{i}",
                folders=[
                    FolderCoverageDetail(folder_name="vanilla", is_merged=True, merge_date=None),
                    FolderCoverageDetail(folder_name="MET", is_merged=False, merge_date=None),
                    FolderCoverageDetail(folder_name="AMO", is_merged=True, merge_date=None),
                ],
                coverage_pct=66.67,
                status="PARTIAL"
            )
        )
    base_context.coverage_matrix.rows = rows

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-009"
    assert violations[0].folder_name == "MET"


def test_gov_010_zero_propagation(base_context) -> None:
    rule = ZeroPropagationRule()
    assert len(rule.evaluate(base_context)) == 0

    # Jira-1 only merged in vanilla, initial commit was 15 days ago (threshold 14 days)
    base_context.delays[0].folder_merge_dates = {"vanilla": datetime.now(timezone.utc), "MET": None, "AMO": None}
    base_context.delays[0].initial_commit_date = datetime.now(timezone.utc) - timedelta(days=15)

    violations = rule.evaluate(base_context)
    assert len(violations) == 1
    assert violations[0].rule_id == "GOV-010"
    assert violations[0].jira_id == "JIRA-1"


@pytest.mark.asyncio
async def test_violation_acknowledgement(monkeypatch) -> None:
    db_mock = MagicMock()
    db_mock.add = MagicMock()
    db_mock.commit = AsyncMock()
    db_mock.refresh = AsyncMock()
    service = ExceptionDetectionService()

    violation = RuleViolation(
        id=uuid.uuid4(),
        repository_id=REPO_ID,
        rule_id="GOV-001",
        severity="CRITICAL",
        category="COVERAGE",
        description="test description",
        is_acknowledged=False
    )
    monkeypatch.setattr(violation_repo, "get", AsyncMock(return_value=violation))

    res = await service.acknowledge_violation(db_mock, violation.id, "developer-1", "acknowledged note")
    assert res.is_success is True
    assert res.value.is_acknowledged is True
    assert res.value.acknowledged_by == "developer-1"
    assert res.value.acknowledge_note == "acknowledged note"
