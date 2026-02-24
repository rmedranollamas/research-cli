import pytest
from research_cli.utils import save_report_to_file, async_save_report_to_file, print_report

def test_save_report_to_file_success(tmp_path):
    """Test that save_report_to_file successfully saves a report when the file doesn't exist."""
    report = "Test report content"
    output_file = tmp_path / "report.md"

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

    result = save_report_to_file(report, str(output_file), force=True)
    assert result is True
    # Content should have changed
    assert output_file.read_text() == report

def test_save_report_to_file_custom_prefix(tmp_path, capsys):
    """Test that save_report_to_file uses the provided success_prefix."""
    report = "Test report content"
    custom_prefix = "SUCCESS: Report written to"
    output_file = tmp_path / "report.md"

    result = save_report_to_file(report, str(output_file), force=False, success_prefix=custom_prefix)
    assert result is True
    captured = capsys.readouterr()
    # MockConsole writes to sys.stdout. Check if custom_prefix and output_file are in the output
    assert custom_prefix in captured.out
    assert str(output_file) in captured.out

def test_print_report(capsys):
    """Test that print_report prints the report to the console."""
    report_text = "Test Report"
    print_report(f"# {report_text}")
    captured = capsys.readouterr()
    assert "=" * 40 in captured.out
    # Check for rendered Markdown content in output
    assert report_text in captured.out

@pytest.mark.asyncio
async def test_async_save_report_to_file(tmp_path):
    """Test that async_save_report_to_file correctly wraps the synchronous function."""
    report = "Async test report content"
    output_file = tmp_path / "report.md"

    result = await async_save_report_to_file(report, str(output_file), force=False)
    assert result is True
    assert output_file.exists()
    assert output_file.read_text() == report
