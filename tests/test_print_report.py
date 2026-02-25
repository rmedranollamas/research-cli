from unittest.mock import patch, MagicMock, call
from research_cli.utils import print_report


@patch("research_cli.utils.get_console")
@patch("rich.markdown.Markdown")
def test_print_report_structure(MockMarkdown, mock_get_console):
    """Test that print_report follows the correct structure: separator, markdown, separator."""
    mock_console = MagicMock()
    mock_get_console.return_value = mock_console

    report_text = "Test Report Content"
    mock_md_instance = MagicMock()
    MockMarkdown.return_value = mock_md_instance

    print_report(report_text)

    # 1. Verify Markdown was instantiated with the report text
    MockMarkdown.assert_called_once_with(report_text)

    # 2. Verify console.print was called with separators and markdown instance
    separator = "\n" + "=" * 40 + "\n"
    expected_calls = [call(separator), call(mock_md_instance), call(separator)]
    mock_console.print.assert_has_calls(expected_calls)
    assert mock_console.print.call_count == 3


@patch("research_cli.utils.get_console")
@patch("rich.markdown.Markdown")
def test_print_report_empty(MockMarkdown, mock_get_console):
    """Test that print_report handles an empty report correctly."""
    mock_console = MagicMock()
    mock_get_console.return_value = mock_console

    print_report("")

    MockMarkdown.assert_called_once_with("")
    assert mock_console.print.call_count == 3


@patch("research_cli.utils.get_console")
@patch("rich.markdown.Markdown")
def test_print_report_long(MockMarkdown, mock_get_console):
    """Test that print_report handles a long report correctly."""
    mock_console = MagicMock()
    mock_get_console.return_value = mock_console

    long_report = "Long " * 1000
    print_report(long_report)

    MockMarkdown.assert_called_once_with(long_report)
    assert mock_console.print.call_count == 3
