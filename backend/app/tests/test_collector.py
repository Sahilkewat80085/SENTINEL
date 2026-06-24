from app.services.commit_collector import CommitCollectorService


def test_extract_jira_ids() -> None:
    """Test extracting Jira IDs from commit messages using configured patterns."""
    service = CommitCollectorService()
    patterns = [r"[A-Z]{2,10}-\d{3,6}"]

    # Standard commit message
    msg = "[NC-4928] fix: resolve content drift in config settings"
    assert service.extract_jira_ids(msg, patterns) == ["NC-4928"]

    # Multiple tickets in one message
    msg2 = "Merge branch NC-5011 and AMO-1209 configurations"
    extracted = service.extract_jira_ids(msg2, patterns)
    assert len(extracted) == 2
    assert "NC-5011" in extracted
    assert "AMO-1209" in extracted

    # Message without ticket
    msg3 = "chores: update README documentation"
    assert service.extract_jira_ids(msg3, patterns) == ["SEN-100"]


def test_map_file_to_folder() -> None:
    """Test mapping file paths to configured release folders."""
    service = CommitCollectorService()
    folders = ["vanilla", "MET", "AMO", "JCF"]

    # Valid matches
    assert service.map_file_to_folder("vanilla/configs/settings.yaml", folders) == "vanilla"
    assert service.map_file_to_folder("MET/deploy/params.json", folders) == "MET"

    # Match in subdirectory should not map as root
    assert service.map_file_to_folder("src/vanilla/main.py", folders) is None

    # Invalid folders
    assert service.map_file_to_folder("UNKNOWN/configs/settings.yaml", folders) is None
