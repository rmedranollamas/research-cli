import pytest
from unittest.mock import patch, MagicMock
from research_cli.utils import escape_markup

def test_escape_markup_fallback():
    # Patch the cached escape function to None to simulate missing dependency
    with patch("research_cli.utils._rich_escape", None):
        text = "[bold]hello[/bold]"
        # It should return the original text
        assert escape_markup(text) == text

def test_escape_markup_with_rich():
    # Simulate rich being present by patching with a mock
    mock_escape = MagicMock(side_effect=lambda x: f"escaped_{x}")
    with patch("research_cli.utils._rich_escape", mock_escape):
        text = "[bold]hello[/bold]"
        assert escape_markup(text) == "escaped_[bold]hello[/bold]"
        mock_escape.assert_called_once_with(text)
