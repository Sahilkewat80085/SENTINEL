from datetime import datetime, timedelta, timezone
from app.services.jira_aggregation import JiraAggregationService


def test_classify_status() -> None:
    """Test classification of Jira issue lifecycle based on its last commit date."""
    service = JiraAggregationService()

    # Timezone-aware date for safety
    now = datetime.now(timezone.utc)

    # 1. ACTIVE: <= 7 days
    active_date = now - timedelta(days=2)
    assert service.classify_status(active_date) == "ACTIVE"

    # 2. STALE: 8-30 days
    stale_date = now - timedelta(days=15)
    assert service.classify_status(stale_date) == "STALE"

    # 3. DORMANT: 31-90 days
    dormant_date = now - timedelta(days=45)
    assert service.classify_status(dormant_date) == "DORMANT"

    # 4. ARCHIVED: > 90 days
    archived_date = now - timedelta(days=120)
    assert service.classify_status(archived_date) == "ARCHIVED"


def test_classify_status_naive_datetime() -> None:
    """Test classification with naive datetimes to verify conversion safety."""
    service = JiraAggregationService()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    active_date = now_naive - timedelta(days=5)
    assert service.classify_status(active_date) == "ACTIVE"

    archived_date = now_naive - timedelta(days=100)
    assert service.classify_status(archived_date) == "ARCHIVED"
