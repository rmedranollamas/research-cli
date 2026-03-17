import pytest
from unittest.mock import MagicMock
from research_cli.utils import get_console, set_console
import research_cli.utils

def test_set_console():
    """Test that set_console correctly sets the console singleton."""
    # Save original console
    original_console = research_cli.utils._console

    try:
        mock_console = MagicMock()
        set_console(mock_console)

        assert get_console() is mock_console

        # Reset and check if it re-initializes (get_console should create a new one if _console is None)
        set_console(None)
        new_console = get_console()
        assert new_console is not None
        assert new_console is not mock_console

    finally:
        # Restore original console
        research_cli.utils._console = original_console

def test_set_console_direct():
    """Trivial test as requested: call it with a mock and verify _console is set."""
    # Save original console
    original_console = research_cli.utils._console

    try:
        mock_console = MagicMock()
        set_console(mock_console)
        assert research_cli.utils._console is mock_console
    finally:
        # Restore original console
        research_cli.utils._console = original_console
