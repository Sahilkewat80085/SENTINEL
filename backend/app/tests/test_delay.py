import pytest

from app.services.merge_delay import MergeDelayService


def test_percentile_calculation() -> None:
    """Test the percentile calculation function in MergeDelayService."""
    service = MergeDelayService()

    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    # 50th percentile (median) should be 5.5
    assert service._percentile(values, 50.0) == pytest.approx(5.5)

    # 95th percentile should be 9.55
    assert service._percentile(values, 95.0) == pytest.approx(9.55)

    # Empty values check
    assert service._percentile([], 95.0) == 0.0

    # Single value check
    assert service._percentile([4.2], 95.0) == pytest.approx(4.2)
