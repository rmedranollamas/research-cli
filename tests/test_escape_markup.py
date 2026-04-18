import pytest
import sys
import importlib
from unittest.mock import patch, MagicMock
import research_cli.utils

@pytest.fixture
def reload_utils():
    """Fixture to ensure research_cli.utils is reloaded after a test that might change its state."""
    yield
    importlib.reload(research_cli.utils)

def test_escape_markup_fallback(reload_utils):
    """Verify that escape_markup returns text as-is when rich is missing at import time."""
    with patch.dict(sys.modules, {"rich.markup": None}):
        importlib.reload(research_cli.utils)

        # Verify module level variable
        assert research_cli.utils._rich_escape is None

        text = "[bold]hello[/bold]"
        # It should return the original text
        assert research_cli.utils.escape_markup(text) == text

def test_escape_markup_with_rich(reload_utils):
    """Verify that escape_markup uses rich.markup.escape when rich is present."""
    mock_markup = MagicMock()
    mock_escape = MagicMock(side_effect=lambda x: f"escaped_{x}")
    mock_markup.escape = mock_escape

    # We patch rich.markup in sys.modules and then reload to ensure _rich_escape picks it up
    with patch.dict(sys.modules, {"rich.markup": mock_markup}):
        importlib.reload(research_cli.utils)

        # Verify it's using our mock
        assert research_cli.utils._rich_escape is mock_escape

        text = "[bold]hello[/bold]"
        assert research_cli.utils.escape_markup(text) == "escaped_[bold]hello[/bold]"
        mock_escape.assert_called_once_with(text)

def test_escape_markup_runtime_patch():
    """Verify that escape_markup respects runtime changes to _rich_escape (simple unit test)."""
    # Save original
    original_escape = research_cli.utils._rich_escape
    try:
        research_cli.utils._rich_escape = None
        text = "test"
        assert research_cli.utils.escape_markup(text) == text

        mock_escape = MagicMock(return_value="escaped")
        research_cli.utils._rich_escape = mock_escape
        assert research_cli.utils.escape_markup("test") == "escaped"
        mock_escape.assert_called_with("test")
    finally:
        # Restore
        research_cli.utils._rich_escape = original_escape
