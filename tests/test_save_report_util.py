from unittest.mock import patch
from research_cli.utils import save_report_to_file, async_save_report_to_file


def test_save_report_to_file_success(tmp_path):
    """Test that save_report_to_file successfully saves a report when the file doesn't exist."""
    report = "Test report content"
    output_file = tmp_path / "report.md"

    # Mock WORKSPACE_DIR to allow saving to tmp_path
    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        result = save_report_to_file(report, str(output_file), force=False)
        assert result is True
        assert output_file.exists()
        assert output_file.read_text() == report


def test_save_report_to_file_exists_no_force(tmp_path):
    """Test that save_report_to_file returns False when the file exists and force is False."""
    report = "New report content"
    existing_content = "Existing content"
    output_file = tmp_path / "report.md"
    output_file.write_text(existing_content)

    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        result = save_report_to_file(report, str(output_file), force=False)
        assert result is False
        # Content should not have changed
        assert output_file.read_text() == existing_content


def test_save_report_to_file_exists_force(tmp_path):
    """Test that save_report_to_file overwrites the file when force is True."""
    report = "New report content"
    existing_content = "Existing content"
    output_file = tmp_path / "report.md"
    output_file.write_text(existing_content)

    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        result = save_report_to_file(report, str(output_file), force=True)
        assert result is True
        # Content should have changed
        assert output_file.read_text() == report


def test_save_report_to_file_custom_prefix(tmp_path, capsys):
    """Test that save_report_to_file uses the provided success_prefix."""
    report = "Test report content"
    custom_prefix = "SUCCESS: Report written to"
    output_file = tmp_path / "report.md"

    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        result = save_report_to_file(
            report, str(output_file), force=False, success_prefix=custom_prefix
        )
        assert result is True
        captured = capsys.readouterr()
        # MockConsole writes to sys.stdout. Check if custom_prefix and output_file are in the output
        assert custom_prefix in captured.out
        # After security fix, we expect sanitized (relative) path
        assert output_file.name in captured.out


def test_async_save_report_to_file(tmp_path):
    """Test that async_save_report_to_file correctly wraps the synchronous function."""
    import asyncio
    report = "Async test report content"
    output_file = tmp_path / "report.md"

    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        result = asyncio.run(async_save_report_to_file(report, str(output_file), force=False))
        assert result is True
        assert output_file.exists()
        assert output_file.read_text() == report
