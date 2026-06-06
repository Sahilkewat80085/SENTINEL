import uuid
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.governance_score import GovernanceScoreService
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.core.result import ServiceResult
from app.schemas.coverage import CoverageSummary
from app.schemas.violation import ViolationSummary
from app.schemas.delay import DelayStatistics
from app.schemas.folder import FolderHealthResult
from app.models.repository import Repository
from app.models.violation import RuleViolation
from app.repositories import repository_repo, violation_repo


REPO_ID = uuid.UUID("bc3f3f3f-4f4f-4f4f-4f4f-4f4f4f4f4f4f")


def test_security_helpers() -> None:
    """Test standard JWT signing/decoding and bcrypt hashing helpers."""
    # 1. Hashing
    pwd = "secret_password"
    pwd_hash = get_password_hash(pwd)
    assert verify_password(pwd, pwd_hash) is True
    assert verify_password("wrong_pwd", pwd_hash) is False

    # 2. JWT Tokens
    username = "admin_user"
    token = create_access_token(subject=username, expires_delta=timedelta(minutes=5))
    decoded_sub = decode_token(token)
    assert decoded_sub == username

    # Expired token test
    expired_token = create_access_token(subject=username, expires_delta=timedelta(minutes=-5))
    assert decode_token(expired_token) is None


@pytest.mark.asyncio
async def test_composite_governance_score_math(monkeypatch) -> None:
    """Test composite governance rating arithmetic and penalty offsets."""
    db_mock = AsyncMock()
    
    # Mock Repository
    repo = Repository(id=REPO_ID, name="test-repo", folders=["vanilla", "MET"])
    monkeypatch.setattr(repository_repo, "get", AsyncMock(return_value=repo))

    # Mock health details:
    # vanilla health = 100.0, MET health = 80.0
    # Average health score = 90.0
    health_service_mock = MagicMock()
    folder_health = [
        FolderHealthResult(
            folder_name="vanilla", coverage_score=100.0, consistency_score=100.0,
            timeliness_score=100.0, completeness_score=100.0, health_score=100.0,
            classification="EXCELLENT"
        ),
        FolderHealthResult(
            folder_name="MET", coverage_score=80.0, consistency_score=80.0,
            timeliness_score=80.0, completeness_score=80.0, health_score=80.0,
            classification="GOOD"
        )
    ]
    health_service_mock.compute_all_health = AsyncMock(return_value=ServiceResult.success(folder_health))

    # Mock active violations:
    # 1 CRITICAL (-5.0 points)
    # 1 HIGH (-3.0 points)
    # Total penalty = 8.0 points
    # Expected score = 90.0 - 8.0 = 82.0 (Grade B)
    violations = [
        RuleViolation(severity="CRITICAL", is_acknowledged=False, resolved_at=None),
        RuleViolation(severity="HIGH", is_acknowledged=False, resolved_at=None),
    ]
    violation_service_mock = MagicMock()
    violation_sum = ViolationSummary(total_violations=2, critical_count=1, high_count=1, medium_count=0, low_count=0, acknowledged_count=0, unacknowledged_count=2, by_category={})
    violation_service_mock.get_violation_summary = AsyncMock(return_value=ServiceResult.success(violation_sum))
    violation_service_mock.get_violations = AsyncMock(return_value=ServiceResult.success(violations))

    service = GovernanceScoreService(
        health_service=health_service_mock,
        violation_service=violation_service_mock
    )

    res = await service.compute_repository_score(db_mock, REPO_ID)
    assert res.is_success is True
    
    score_detail = res.value
    assert score_detail.score == 82.0
    assert score_detail.grade == "B"
    assert score_detail.folder_health_average == 90.0
    assert score_detail.violation_penalty == 8.0
    assert score_detail.active_critical_count == 1
    assert score_detail.active_high_count == 1
