import sys
import importlib
from unittest.mock import patch, mock_open
from importlib import metadata
import pytest
import argparse


def test_get_version_import_error_tomllib():
    """Verify that get_version() handles ImportError when tomllib is missing."""
    with patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        with patch("pathlib.Path.exists", return_value=True):
            with patch.dict(sys.modules, {"tomllib": None}):
                # Reload to re-evaluate get_version logic
                if "research_cli.cli" in sys.modules:
                    importlib.reload(sys.modules["research_cli.cli"])
                from research_cli.cli import get_version

                # Should return "unknown" due to tomllib ImportError
                assert get_version() == "unknown"


def test_get_version_unexpected_error():
    """Verify that get_version() handles unexpected errors like KeyError."""
    with patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        with patch("pathlib.Path.exists", return_value=True):
            # Mock tomllib.load to raise KeyError
            if "research_cli.cli" in sys.modules:
                importlib.reload(sys.modules["research_cli.cli"])
            from research_cli.cli import get_version

            # Mock tomllib.load to raise KeyError
            with patch("builtins.open", mock_open(read_data=b"[invalid]\n")):
                with patch("tomllib.load", side_effect=KeyError("project")):
                    assert get_version() == "unknown"


def test_create_parser_without_dotenv():
    """Verify that create_parser() still works when the dotenv package is missing."""
    # We need to mock the google modules because importing cli will import researcher
    with patch.dict(sys.modules, {"dotenv": None}):
        # Check if we can still call create_parser
        if "research_cli.cli" in sys.modules:
            importlib.reload(sys.modules["research_cli.cli"])
        from research_cli.cli import create_parser

        parser, script_name = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert "Gemini Deep Research CLI" in parser.description


@pytest.fixture(autouse=True)
def cleanup_cli():
    yield
    # Restore original state
    if "research_cli.config" in sys.modules:
        importlib.reload(sys.modules["research_cli.config"])
    if "research_cli.cli" in sys.modules:
        importlib.reload(sys.modules["research_cli.cli"])
