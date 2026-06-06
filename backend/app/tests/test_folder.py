import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.folder_health import FolderHealthService
from app.schemas.folder import FolderHealthResult
from app.core.result import ServiceResult
from app.schemas.coverage import CoverageMatrix, JiraCoverageRow, FolderCoverageDetail
from app.schemas.content import DriftReport, ContentVerificationResult
from app.schemas.delay import DelayStatistics, FolderDelayRank
from app.models.repository import Repository
from app.repositories import repository_repo


# Valid static UUID for testing purposes
REPO_ID = uuid.UUID("7c3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f")


def test_classify_health_logic() -> None:
    """Test standard health classification bands in FolderHealthService."""
    service = FolderHealthService()
    
    assert service._classify_health(95.0) == "EXCELLENT"
    assert service._classify_health(90.0) == "EXCELLENT"
    assert service._classify_health(89.9) == "GOOD"
    assert service._classify_health(70.0) == "GOOD"
    assert service._classify_health(69.9) == "WARNING"
    assert service._classify_health(50.0) == "WARNING"
    assert service._classify_health(49.9) == "POOR"
    assert service._classify_health(25.0) == "POOR"
    assert service._classify_health(24.9) == "CRITICAL"
    assert service._classify_health(0.0) == "CRITICAL"


@pytest.mark.asyncio
async def test_folder_health_scoring_logic(monkeypatch) -> None:
    """Test folder health score formulas, weights, and results structure."""
    db_mock = AsyncMock()
    
    # Mock Repository
    repo = Repository(id=REPO_ID, name="test-repo", folders=["vanilla", "MET", "AMO"])
    monkeypatch.setattr(repository_repo, "get", AsyncMock(return_value=repo))
    
    # Mock coverage service
    coverage_service_mock = MagicMock()
    coverage_rows = [
        JiraCoverageRow(
            jira_id="JIRA-1",
            folders=[
                FolderCoverageDetail(folder_name="vanilla", is_merged=True, merge_date=None),
                FolderCoverageDetail(folder_name="MET", is_merged=False, merge_date=None),
                FolderCoverageDetail(folder_name="AMO", is_merged=True, merge_date=None),
            ],
            coverage_pct=66.67,
            status="PARTIAL"
        )
    ]
    coverage_matrix = CoverageMatrix(repository_id=REPO_ID, folders_list=["vanilla", "MET", "AMO"], rows=coverage_rows)
    coverage_service_mock.get_coverage_matrix_data = AsyncMock(return_value=ServiceResult.success(coverage_matrix))
    
    # Mock content verification service
    content_service_mock = MagicMock()
    drifted_files = [
        ContentVerificationResult(
            file_path="configs/settings.yaml",
            status="DIFFERENT",
            drift_score=0.33,
            folder_hashes={"vanilla": "sha1", "MET": "sha1", "AMO": "sha2"},
            majority_hash="sha1",
            divergent_folders=["AMO"],
            file_sizes={"vanilla": 100, "MET": 100, "AMO": 100}
        )
    ]
    drift_report = DriftReport(drifted_files=drifted_files, overall_drift_score=0.33)
    content_service_mock.get_drift_report_data = AsyncMock(return_value=ServiceResult.success(drift_report))
    
    # Mock delay service
    delay_service_mock = MagicMock()
    delay_stats = DelayStatistics(
        overall_avg_delay_days=5.33,
        overall_max_delay_days=10.0,
        status_distribution={"HEALTHY": 2, "WARNING": 1, "CRITICAL": 0},
        folder_rankings=[
            FolderDelayRank(folder_name="vanilla", avg_delay_days=1.0, max_delay_days=1.0, p95_delay_days=1.0),
            FolderDelayRank(folder_name="MET", avg_delay_days=10.0, max_delay_days=10.0, p95_delay_days=10.0),
            FolderDelayRank(folder_name="AMO", avg_delay_days=5.0, max_delay_days=5.0, p95_delay_days=5.0),
        ]
    )
    delay_service_mock.get_delay_statistics_data = AsyncMock(return_value=ServiceResult.success(delay_stats))
    
    # Mock db.execute for:
    # 1. folder file counts
    # 2. total unique files count
    mock_execute_results = [
        MagicMock(all=MagicMock(return_value=[("vanilla", 2), ("MET", 2), ("AMO", 2)])),
        MagicMock(scalar=MagicMock(return_value=2))
    ]
    db_mock.execute = AsyncMock(side_effect=mock_execute_results)
    
    # Instantiate service
    service = FolderHealthService(
        coverage_service=coverage_service_mock,
        content_service=content_service_mock,
        delay_service=delay_service_mock
    )
    
    # Run
    res = await service.compute_all_health(db_mock, REPO_ID)
    assert res.is_success is True
    results = res.value
    assert len(results) == 3
    
    # Verify vanilla calculations
    # coverage = 100.0, consistency = 100.0, timeliness = 97.0 (100 - 1*3), completeness = 100.0 (2/2)
    # health = 100 * 0.35 + 100 * 0.30 + 97 * 0.20 + 100 * 0.15 = 99.4
    vanilla = next(r for r in results if r.folder_name == "vanilla")
    assert vanilla.coverage_score == 100.0
    assert vanilla.consistency_score == 100.0
    assert vanilla.timeliness_score == 97.0
    assert vanilla.completeness_score == 100.0
    assert vanilla.health_score == pytest.approx(99.4)
    assert vanilla.classification == "EXCELLENT"
    
    # Verify MET calculations
    # coverage = 0.0, consistency = 100.0, timeliness = 70.0 (100 - 10*3), completeness = 100.0 (2/2)
    # health = 0 * 0.35 + 100 * 0.30 + 70 * 0.20 + 100 * 0.15 = 59.0
    met = next(r for r in results if r.folder_name == "MET")
    assert met.coverage_score == 0.0
    assert met.consistency_score == 100.0
    assert met.timeliness_score == 70.0
    assert met.completeness_score == 100.0
    assert met.health_score == pytest.approx(59.0)
    assert met.classification == "WARNING"

    # Verify AMO calculations
    # coverage = 100.0, consistency = 50.0 (1 drifted out of 2), timeliness = 85.0 (100 - 5*3), completeness = 100.0 (2/2)
    # health = 100 * 0.35 + 50 * 0.30 + 85 * 0.20 + 100 * 0.15 = 35 + 15 + 17 + 15 = 82.0
    amo = next(r for r in results if r.folder_name == "AMO")
    assert amo.coverage_score == 100.0
    assert amo.consistency_score == 50.0
    assert amo.timeliness_score == 85.0
    assert amo.completeness_score == 100.0
    assert amo.health_score == pytest.approx(82.0)
    assert amo.classification == "GOOD"


@pytest.mark.asyncio
async def test_folder_health_ranking_and_heatmap(monkeypatch) -> None:
    """Test ranking and heatmap formatting logic."""
    db_mock = AsyncMock()
    service = FolderHealthService()
    
    # Mock compute_all_health
    mock_results = [
        FolderHealthResult(
            folder_name="vanilla",
            coverage_score=100.0,
            consistency_score=100.0,
            timeliness_score=97.0,
            completeness_score=100.0,
            health_score=99.4,
            classification="EXCELLENT"
        ),
        FolderHealthResult(
            folder_name="MET",
            coverage_score=0.0,
            consistency_score=100.0,
            timeliness_score=70.0,
            completeness_score=100.0,
            health_score=59.0,
            classification="WARNING"
        ),
        FolderHealthResult(
            folder_name="AMO",
            coverage_score=100.0,
            consistency_score=50.0,
            timeliness_score=85.0,
            completeness_score=100.0,
            health_score=82.0,
            classification="GOOD"
        )
    ]
    service.compute_all_health = AsyncMock(return_value=ServiceResult.success(mock_results))
    
    # Test Rankings (should sort descending: vanilla, AMO, MET)
    rank_res = await service.get_health_ranking(db_mock, REPO_ID)
    assert rank_res.is_success is True
    rankings = rank_res.value
    assert len(rankings) == 3
    assert rankings[0].folder_name == "vanilla"
    assert rankings[0].rank == 1
    assert rankings[1].folder_name == "AMO"
    assert rankings[1].rank == 2
    assert rankings[2].folder_name == "MET"
    assert rankings[2].rank == 3
    
    # Test Weakest Folders
    weak_res = await service.get_weakest_folders(db_mock, REPO_ID, n=2)
    assert weak_res.is_success is True
    weakest = weak_res.value
    assert len(weakest) == 2
    assert weakest[0].folder_name == "MET"  # lowest score first
    assert weakest[1].folder_name == "AMO"

    # Test Heatmap Data
    heatmap_res = await service.get_heatmap_data(db_mock, REPO_ID)
    assert heatmap_res.is_success is True
    cells = heatmap_res.value
    # 3 folders * 5 metrics = 15 cells
    assert len(cells) == 15
    vanilla_cov = next(c for c in cells if c.folder_name == "vanilla" and c.metric == "coverage")
    assert vanilla_cov.score == 100.0
