import sys
import importlib
from unittest.mock import patch
from importlib import metadata
import pytest

def test_version_metadata_found():
    with patch("importlib.metadata.version", return_value="1.2.3"):
        # We need to reload the module to re-evaluate the VERSION assignment
        if "research_cli.cli" in sys.modules:
            importlib.reload(sys.modules["research_cli.cli"])
        from research_cli import cli
        assert cli.VERSION == "1.2.3"

def test_version_metadata_not_found():
    with patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        # We need to reload the module to re-evaluate the VERSION assignment
        if "research_cli.cli" in sys.modules:
            importlib.reload(sys.modules["research_cli.cli"])
        from research_cli import cli
        assert cli.VERSION == "0.1.45"

# Clean up after tests to avoid affecting other tests
@pytest.fixture(autouse=True)
def cleanup_cli():
    yield
    if "research_cli.cli" in sys.modules:
        importlib.reload(sys.modules["research_cli.cli"])
