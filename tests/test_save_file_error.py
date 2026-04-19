import pytest
from unittest.mock import patch
from research_cli.utils import save_report_to_file, save_binary_to_file

def test_save_report_to_file_exception(tmp_path, capsys):
    """Test that save_report_to_file handles exceptions during file writing."""
    report = "Test report content"
    output_file = tmp_path / "report.md"

    # Mock WORKSPACE_DIR to allow saving to tmp_path
    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        # Mock os.open to raise an exception
        with patch("os.open", side_effect=PermissionError("Permission denied")):
            result = save_report_to_file(report, str(output_file), force=False)

            assert result is False
            captured = capsys.readouterr()
            assert "Error saving to file" in captured.out
            assert "Permission denied" in captured.out

def test_save_binary_to_file_exception(tmp_path, capsys):
    """Test that save_binary_to_file handles exceptions during file writing."""
    data = b"binary data"
    output_file = tmp_path / "test.bin"

    # Mock WORKSPACE_DIR to allow saving to tmp_path
    with patch("research_cli.utils.WORKSPACE_DIR", str(tmp_path)):
        # Mock os.open to raise an exception
        with patch("os.open", side_effect=OSError("Disk full")):
            result = save_binary_to_file(data, str(output_file), force=False)

            assert result is False
            captured = capsys.readouterr()
            assert "Error saving to file" in captured.out
            assert "Disk full" in captured.out
