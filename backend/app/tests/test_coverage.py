from app.schemas.coverage import FolderCoverageDetail, JiraCoverageRow


def test_coverage_status_classification() -> None:
    """Test manual/algorithmic classification rules matching system metrics design."""
    # Helper lambda to simulate service logic
    def get_status(coverage_pct: float) -> str:
        if coverage_pct == 100.0:
            return "MERGED"
        elif coverage_pct == 0.0:
            return "MISSING"
        else:
            return "PARTIAL"

    # Test cases
    assert get_status(100.0) == "MERGED"
    assert get_status(0.0) == "MISSING"
    assert get_status(50.0) == "PARTIAL"
    assert get_status(99.9) == "PARTIAL"


def test_coverage_row_initialization() -> None:
    """Test creating and validating schema rows representing individual issue coverages."""
    folders = [
        FolderCoverageDetail(folder_name="vanilla", is_merged=True, merge_date=None),
        FolderCoverageDetail(folder_name="MET", is_merged=False, merge_date=None),
    ]

    row = JiraCoverageRow(
        jira_id="NC-4928",
        folders=folders,
        coverage_pct=50.0,
        status="PARTIAL",
    )

    assert row.jira_id == "NC-4928"
    assert len(row.folders) == 2
    assert row.folders[0].folder_name == "vanilla"
    assert row.folders[0].is_merged is True
    assert row.folders[1].folder_name == "MET"
    assert row.folders[1].is_merged is False
    assert row.coverage_pct == 50.0
    assert row.status == "PARTIAL"
