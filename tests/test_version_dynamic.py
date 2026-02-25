import sys
import importlib
from unittest.mock import patch, mock_open
from importlib import metadata
import pytest


def test_version_metadata_found():
    with patch("importlib.metadata.version", return_value="1.2.3"):
        # We need to reload the module to re-evaluate the VERSION assignment
        if "research_cli.cli" in sys.modules:
            importlib.reload(sys.modules["research_cli.cli"])
        from research_cli import cli

        assert cli.VERSION == "1.2.3"


def test_version_from_pyproject():
    # Mock PackageNotFoundError and mock existence of pyproject.toml
    mock_toml = b'[project]\nname = "research-cli"\nversion = "2.0.0"\n'
    with patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_toml)):
                if "research_cli.cli" in sys.modules:
                    importlib.reload(sys.modules["research_cli.cli"])
                from research_cli import cli

                assert cli.VERSION == "2.0.0"


def test_version_fallback_unknown():
    with patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        with patch("pathlib.Path.exists", return_value=False):
            if "research_cli.cli" in sys.modules:
                importlib.reload(sys.modules["research_cli.cli"])
            from research_cli import cli

            assert cli.VERSION == "unknown"


# Clean up after tests to avoid affecting other tests
@pytest.fixture(autouse=True)
def cleanup_cli():
    yield
    if "research_cli.cli" in sys.modules:
        importlib.reload(sys.modules["research_cli.cli"])
