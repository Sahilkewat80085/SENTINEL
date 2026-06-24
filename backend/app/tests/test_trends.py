import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.trends import parse_period_to_days
from app.core.result import ServiceResult
from app.models.repository import Repository
from app.models.snapshot import GovernanceSnapshot
from app.repositories import repository_repo, snapshot_repo
from app.schemas.coverage import CoverageSummary
from app.schemas.delay import DelayStatistics
from app.schemas.folder import FolderHealthResult
from app.schemas.violation import ViolationSummary
from app.services.trend_analytics import TrendAnalyticsService

REPO_ID = uuid.UUID("9c3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f")


def test_parse_period_to_days() -> None:
    """Test helper parsing period duration strings to days count."""
    assert parse_period_to_days("7d") == 7
    assert parse_period_to_days("30D") == 30
    assert parse_period_to_days("12w") == 84
    assert parse_period_to_days("2m") == 60
    assert parse_period_to_days("random") == 30
    assert parse_period_to_days("") == 30


@pytest.mark.asyncio
async def test_capture_daily_snapshot(monkeypatch) -> None:
    """Test full pipeline of capturing daily snapshots and updating DB."""
    db_mock = MagicMock()
    db_mock.execute = AsyncMock()
    db_mock.commit = AsyncMock()
    db_mock.flush = AsyncMock()

    # Mocks
    repo = Repository(id=REPO_ID, name="test-repo", folders=["vanilla", "MET"])
    monkeypatch.setattr(repository_repo, "get", AsyncMock(return_value=repo))

    cov_service_mock = MagicMock()
    cov_sum = CoverageSummary(total_jiras=10, merged_count=8, partial_count=1, missing_count=1, overall_coverage_pct=85.0)
    cov_service_mock.get_coverage_summary_data = AsyncMock(return_value=ServiceResult.success(cov_sum))
    cov_service_mock.get_missing_merges_list = AsyncMock(return_value=ServiceResult.success([]))

    delay_service_mock = MagicMock()
    delay_stats = DelayStatistics(overall_avg_delay_days=4.5, overall_max_delay_days=10.0, status_distribution={})
    delay_service_mock.get_delay_statistics_data = AsyncMock(return_value=ServiceResult.success(delay_stats))

    health_service_mock = MagicMock()
    folder_health = [
        FolderHealthResult(
            folder_name="vanilla", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        ),
        FolderHealthResult(
            folder_name="MET", coverage_score=70.0, consistency_score=90.0,
            timeliness_score=80.0, completeness_score=80.0, health_score=78.0,
            classification="GOOD"
        )
    ]
    health_service_mock.compute_all_health = AsyncMock(return_value=ServiceResult.success(folder_health))

    violation_service_mock = MagicMock()
    violation_sum = ViolationSummary(total_violations=3, critical_count=1, high_count=1, medium_count=1, low_count=0, acknowledged_count=1, unacknowledged_count=2, by_category={})
    violation_service_mock.get_violation_summary = AsyncMock(return_value=ServiceResult.success(violation_sum))

    # Mock DB counts execute
    mock_execute_res = MagicMock()
    mock_execute_res.scalar_one_or_none = MagicMock(return_value=None)  # no previous snapshots dates
    mock_execute_res.scalar = MagicMock(return_value=15)  # total commits count
    db_mock.execute = AsyncMock(return_value=mock_execute_res)

    # Mock snapshot repository upserts
    monkeypatch.setattr(snapshot_repo, "upsert_governance_snapshot", AsyncMock(return_value=None))
    monkeypatch.setattr(snapshot_repo, "upsert_folder_health_snapshot", AsyncMock(return_value=None))

    service = TrendAnalyticsService(
        coverage_service=cov_service_mock,
        delay_service=delay_service_mock,
        health_service=health_service_mock,
        violation_service=violation_service_mock
    )

    res = await service.capture_daily_snapshot(db_mock, REPO_ID)
    assert res.is_success is True
    assert res.value["status"] == "success"
    assert res.value["date"] == date.today()


@pytest.mark.asyncio
async def test_get_trends_formatting(monkeypatch) -> None:
    """Test compile lists of trends data output structures."""
    db_mock = AsyncMock()
    service = TrendAnalyticsService()

    # Mock snapshots
    snap_date = date.today()
    snap = GovernanceSnapshot(
        repository_id=REPO_ID,
        snapshot_date=snap_date,
        total_jiras=5,
        total_commits=10,
        overall_coverage_pct=90.0,
        avg_delay_days=3.0,
        critical_violation_count=1,
        metadata_info={"high_violation_count": 1, "medium_violation_count": 0, "low_violation_count": 0}
    )
    monkeypatch.setattr(snapshot_repo, "get_governance_snapshots", AsyncMock(return_value=[snap]))

    # Test coverage trend
    cov_res = await service.get_coverage_trend(db_mock, REPO_ID)
    assert cov_res.is_success is True
    assert len(cov_res.value) == 1
    assert cov_res.value[0].date == snap_date
    assert cov_res.value[0].value == 90.0

    # Test delay trend
    delay_res = await service.get_delay_trend(db_mock, REPO_ID)
    assert delay_res.is_success is True
    assert len(delay_res.value) == 1
    assert delay_res.value[0].date == snap_date
    assert delay_res.value[0].value == 3.0

    # Test violation trend
    viol_res = await service.get_violation_trend(db_mock, REPO_ID)
    assert viol_res.is_success is True
    assert len(viol_res.value) == 1
    assert viol_res.value[0].date == snap_date
    assert viol_res.value[0].critical_count == 1
    assert viol_res.value[0].high_count == 1
    assert viol_res.value[0].total_count == 2
