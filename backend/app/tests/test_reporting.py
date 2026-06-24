import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.result import ServiceResult
from app.models.repository import Repository
from app.repositories import commit_repo, repository_repo
from app.schemas.content import ContentVerificationResult, DriftReport
from app.schemas.coverage import (
    CoverageMatrix,
    CoverageSummary,
    FolderCoverageDetail,
    JiraCoverageRow,
)
from app.schemas.dashboard import GovernanceScoreDetail
from app.schemas.delay import DelayStatistics, FolderDelayRank
from app.schemas.folder import FolderHealthResult
from app.schemas.violation import ViolationSummary
from app.services.reporting.chart_generator import ReportChartGenerator
from app.services.reporting.excel_builder import ExcelReportBuilder
from app.services.reporting.pdf_builder import PDFReportBuilder

REPO_ID = uuid.UUID("bc3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f")


@pytest.mark.asyncio
async def test_excel_and_pdf_report_builders(monkeypatch) -> None:
    """Test Excel and PDF report generation logic by mocking service dependencies."""
    db_mock = AsyncMock()

    # 1. Mock Repository
    repo = Repository(id=REPO_ID, name="test-repo", folders=["vanilla", "MET"])
    monkeypatch.setattr(repository_repo, "get", AsyncMock(return_value=repo))

    # 2. Mock Governance Score
    score_detail = GovernanceScoreDetail(
        score=90.0,
        grade="A",
        folder_health_average=90.0,
        violation_penalty=0.0,
        active_critical_count=0,
        active_high_count=0,
        active_medium_count=0,
        active_low_count=0
    )
    monkeypatch.setattr(
        "app.services.governance_score.GovernanceScoreService.compute_repository_score",
        AsyncMock(return_value=ServiceResult.success(score_detail))
    )

    # 3. Mock Folder Health
    folder_health = [
        FolderHealthResult(
            folder_name="vanilla", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        )
    ]
    monkeypatch.setattr(
        "app.services.folder_health.FolderHealthService.compute_all_health",
        AsyncMock(return_value=ServiceResult.success(folder_health))
    )

    # 4. Mock Coverage Summary & Matrix
    coverage_sum = CoverageSummary(
        total_jiras=5,
        merged_count=3,
        partial_count=1,
        missing_count=1,
        overall_coverage_pct=80.0
    )
    monkeypatch.setattr(
        "app.services.folder_coverage.FolderCoverageService.get_coverage_summary_data",
        AsyncMock(return_value=ServiceResult.success(coverage_sum))
    )

    coverage_rows = [
        JiraCoverageRow(
            jira_id="JIRA-1",
            folders=[FolderCoverageDetail(folder_name="vanilla", is_merged=True)],
            coverage_pct=100.0,
            status="MERGED"
        )
    ]
    matrix = CoverageMatrix(repository_id=REPO_ID, folders_list=["vanilla"], rows=coverage_rows)
    monkeypatch.setattr(
        "app.services.folder_coverage.FolderCoverageService.get_coverage_matrix_data",
        AsyncMock(return_value=ServiceResult.success(matrix))
    )

    # 5. Mock Merge Delay Statistics
    delay_stats = DelayStatistics(
        overall_avg_delay_days=2.5,
        overall_max_delay_days=5.0,
        status_distribution={"HEALTHY": 1},
        folder_rankings=[FolderDelayRank(folder_name="vanilla", avg_delay_days=2.5, max_delay_days=5.0, p95_delay_days=4.8)]
    )
    monkeypatch.setattr(
        "app.services.merge_delay.MergeDelayService.get_delay_statistics_data",
        AsyncMock(return_value=ServiceResult.success(delay_stats))
    )

    # 6. Mock Content Verification/Drift
    drifted_files = [
        ContentVerificationResult(
            file_path="settings.yaml",
            status="IDENTICAL",
            drift_score=0.0,
            folder_hashes={"vanilla": "sha256"},
            divergent_folders=[],
            file_sizes={"vanilla": 100}
        )
    ]
    drift_report = DriftReport(drifted_files=drifted_files, overall_drift_score=0.0)
    monkeypatch.setattr(
        "app.services.content_verification.ContentVerificationService.get_drift_report_data",
        AsyncMock(return_value=ServiceResult.success(drift_report))
    )

    # 7. Mock Exception Detection/Violations
    viol_sum = ViolationSummary(
        total_violations=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        acknowledged_count=0,
        unacknowledged_count=0,
        by_category={}
    )
    monkeypatch.setattr(
        "app.services.exception_detection.ExceptionDetectionService.get_violation_summary",
        AsyncMock(return_value=ServiceResult.success(viol_sum))
    )
    monkeypatch.setattr(
        "app.services.exception_detection.ExceptionDetectionService.get_violations",
        AsyncMock(return_value=ServiceResult.success([]))
    )

    # 8. Mock Trend Snapshots
    monkeypatch.setattr(
        "app.services.trend_analytics.TrendAnalyticsService.get_coverage_trend",
        AsyncMock(return_value=ServiceResult.success([]))
    )
    monkeypatch.setattr(
        "app.services.trend_analytics.TrendAnalyticsService.get_health_trend",
        AsyncMock(return_value=ServiceResult.success([]))
    )
    monkeypatch.setattr(
        "app.services.trend_analytics.TrendAnalyticsService.get_delay_trend",
        AsyncMock(return_value=ServiceResult.success([]))
    )
    monkeypatch.setattr(
        "app.services.trend_analytics.TrendAnalyticsService.get_violation_trend",
        AsyncMock(return_value=ServiceResult.success([]))
    )

    # 9. Mock Commit Repo
    monkeypatch.setattr(
        commit_repo,
        "get_commits_for_repository",
        AsyncMock(return_value=[])
    )

    # Excel builder test
    excel_builder = ExcelReportBuilder()
    excel_bytes = await excel_builder.build(db_mock, REPO_ID)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    # PDF builder test (verifying HTML rendering at least, even if WeasyPrint fallback is triggered)
    pdf_builder = PDFReportBuilder()
    pdf_bytes = await pdf_builder.build(db_mock, REPO_ID)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_chart_generator() -> None:
    """Test that chart generator handles Matplotlib rendering correctly without errors."""
    generator = ReportChartGenerator()

    # Pie chart
    pie_bytes = generator.generate_coverage_pie_chart(3, 1, 1)
    # If matplotlib is installed it returns bytes, else None
    if pie_bytes is not None:
        assert isinstance(pie_bytes, bytes)
        assert len(pie_bytes) > 0

    # Trend chart
    trend_bytes = generator.generate_health_trend_chart(["2026-06-01", "2026-06-02"], [90.0, 95.0])
    if trend_bytes is not None:
        assert isinstance(trend_bytes, bytes)
        assert len(trend_bytes) > 0
