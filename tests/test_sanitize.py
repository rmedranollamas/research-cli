import os
from unittest.mock import patch
from research_cli.utils import sanitize_path, sanitize_error

def test_sanitize_path_inside_workspace(tmp_path):
    """Test sanitize_path with a path inside the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file_path = workspace / "subdir" / "test.txt"
    file_path.parent.mkdir()
    file_path.touch()

    # Need to use realpath for workspace because tmp_path might contain symlinks on some OSs (like macOS)
    real_workspace = os.path.realpath(str(workspace))
    real_file_path = os.path.realpath(str(file_path))

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_path(real_file_path)
        assert result == os.path.join("subdir", "test.txt")

def test_sanitize_path_outside_workspace(tmp_path):
    """Test sanitize_path with a path outside the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.touch()

    real_workspace = os.path.realpath(str(workspace))
    real_outside_file = os.path.realpath(str(outside_file))

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_path(real_outside_file)
        assert result == "outside.txt"

def test_sanitize_path_empty():
    """Test sanitize_path with empty input."""
    assert sanitize_path("") == ""
    assert sanitize_path(None) == ""

def test_sanitize_path_exactly_workspace(tmp_path):
    """Test sanitize_path with a path that is exactly the workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_path(real_workspace)
        assert result == "."

def test_sanitize_path_relpath_value_error(tmp_path):
    """Test sanitize_path when os.path.relpath raises ValueError."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))
    file_path = "/abs/path/test.txt"

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        with patch("os.path.relpath", side_effect=ValueError("Different drives")):
            result = sanitize_path(file_path)
            assert result == "test.txt"

def test_sanitize_path_relpath_os_error(tmp_path):
    """Test sanitize_path when os.path.relpath raises OSError."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))
    file_path = "/abs/path/test.txt"

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        with patch("os.path.relpath", side_effect=OSError("Generic error")):
            result = sanitize_path(file_path)
            assert result == "test.txt"

def test_sanitize_path_with_symlinks(tmp_path):
    """Test sanitize_path with symlinks."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))

    # File inside workspace
    target_file = workspace / "target.txt"
    target_file.touch()

    # Symlink inside workspace pointing to file inside workspace
    link_inside = workspace / "link_inside.txt"
    link_inside.symlink_to(target_file)

    # File outside workspace
    outside_file = tmp_path / "outside.txt"
    outside_file.touch()

    # Symlink inside workspace pointing to file outside workspace
    link_outside = workspace / "link_outside.txt"
    link_outside.symlink_to(outside_file)

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        # link_inside should resolve to target.txt relative to workspace
        # because realpath resolves the link
        assert sanitize_path(str(link_inside)) == "target.txt"

        # link_outside should resolve to link_outside.txt (basename of input)
        # because its realpath is outside workspace
        assert sanitize_path(str(link_outside)) == "link_outside.txt"

def test_sanitize_path_with_traversal(tmp_path):
    """Test sanitize_path with path traversal components."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))

    outside_file = tmp_path / "outside.txt"
    outside_file.touch()

    traversal_path = os.path.join(real_workspace, "..", "outside.txt")

    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        # realpath should resolve workspace/../outside.txt to outside.txt
        # and since it is outside workspace, it should return basename
        assert sanitize_path(traversal_path) == "outside.txt"

def test_sanitize_error_basic(tmp_path):
    """Test sanitize_error replaces the original path with the sanitized version."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))
    original_path = os.path.join(real_workspace, "test.txt")

    error_msg = f"Error at {original_path}"
    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        # sanitize_path(original_path) will return "test.txt"
        result = sanitize_error(error_msg, original_path)
        assert result == "Error at test.txt"

def test_sanitize_error_with_realpath(tmp_path):
    """Test sanitize_error replaces the realpath of original_path."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))

    # We'll simulate a situation where the error message uses the absolute real path
    original_path = os.path.join(real_workspace, "test.txt")
    abs_path = os.path.realpath(original_path)

    error_msg = f"Error at {abs_path}"
    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_error(error_msg, original_path)
        assert result == "Error at test.txt"

def test_sanitize_error_workspace_dir(tmp_path):
    """Test sanitize_error replaces the workspace directory with '.'."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))
    original_path = os.path.join(real_workspace, "test.txt")

    error_msg = f"Internal error in {real_workspace}/system"
    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_error(error_msg, original_path)
        assert result == "Internal error in ./system"

def test_sanitize_error_empty():
    """Test sanitize_error with empty error message."""
    assert sanitize_error("", "/some/path") == ""
    assert sanitize_error(None, "/some/path") == ""

def test_sanitize_error_multiple_occurrences(tmp_path):
    """Test sanitize_error with multiple occurrences of the path."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_workspace = os.path.realpath(str(workspace))
    original_path = os.path.join(real_workspace, "test.txt")

    error_msg = f"Failed to open {original_path}. Repeated: {original_path}"
    with patch("research_cli.utils.WORKSPACE_DIR", real_workspace):
        result = sanitize_error(error_msg, original_path)
        assert result == "Failed to open test.txt. Repeated: test.txt"
