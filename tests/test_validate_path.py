import os
import pytest
from unittest.mock import patch
from research_cli.utils import validate_path
from research_cli.config import ResearchError

def test_validate_path_success(tmp_path):
    """Test validate_path with a valid path within the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file_path = workspace / "test.txt"
    file_path.touch()

    with patch("research_cli.utils.WORKSPACE_DIR", str(workspace)):
        resolved_path = validate_path("test.txt")
        assert resolved_path == os.path.realpath(str(file_path))

def test_validate_path_empty():
    """Test validate_path with an empty path."""
    with pytest.raises(ResearchError, match="Empty or invalid path provided"):
        validate_path("")

def test_validate_path_none():
    """Test validate_path with None."""
    with pytest.raises(ResearchError, match="Empty or invalid path provided"):
        validate_path(None)

def test_validate_path_traversal(tmp_path):
    """Test validate_path with a path outside the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.touch()

    with patch("research_cli.utils.WORKSPACE_DIR", str(workspace)):
        with pytest.raises(ResearchError, match="Path traversal detected"):
            validate_path("../outside.txt")

def test_validate_path_value_error(tmp_path):
    """Test validate_path handling ValueError from os.path.commonpath (e.g., different drives)."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with patch("research_cli.utils.WORKSPACE_DIR", str(workspace)):
        with patch("os.path.commonpath", side_effect=ValueError("Paths are on different drives")):
            with pytest.raises(ResearchError, match="on a different volume than the workspace"):
                validate_path("test.txt")

def test_validate_path_absolute_within_workspace(tmp_path):
    """Test validate_path with an absolute path within the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file_path = workspace / "test.txt"
    file_path.touch()

    with patch("research_cli.utils.WORKSPACE_DIR", str(workspace)):
        resolved_path = validate_path(str(file_path))
        assert resolved_path == os.path.realpath(str(file_path))

def test_validate_path_absolute_outside_workspace(tmp_path):
    """Test validate_path with an absolute path outside the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_path = tmp_path / "outside"
    outside_path.mkdir()

    with patch("research_cli.utils.WORKSPACE_DIR", str(workspace)):
        with pytest.raises(ResearchError, match="Path traversal detected"):
            validate_path(str(outside_path))
