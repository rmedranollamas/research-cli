import os
import sqlite3
import pytest
from research import get_db, DB_PATH

def test_db_permissions(tmp_path):
    # Use a temporary database path
    test_db_path = tmp_path / "subdir" / "test.db"

    # Patch DB_PATH in research module
    import research
    original_db_path = research.DB_PATH
    research.DB_PATH = str(test_db_path)

    try:
        with get_db() as conn:
            pass

        # Check directory permissions
        db_dir = os.path.dirname(str(test_db_path))
        dir_mode = os.stat(db_dir).st_mode & 0o777
        assert dir_mode == 0o700, f"Expected directory mode 0700, got {oct(dir_mode)}"

        # Check file permissions
        file_mode = os.stat(str(test_db_path)).st_mode & 0o777
        assert file_mode == 0o600, f"Expected file mode 0600, got {oct(file_mode)}"

    finally:
        research.DB_PATH = original_db_path

def test_db_permissions_existing(tmp_path):
    # Use a temporary database path
    test_db_path = tmp_path / "existing" / "test.db"
    db_dir = os.path.dirname(str(test_db_path))

    # Pre-create directory and file with loose permissions
    os.makedirs(db_dir, mode=0o777, exist_ok=True)
    os.chmod(db_dir, 0o777)
    with open(test_db_path, "w") as f:
        f.write("dummy")
    os.chmod(test_db_path, 0o666)

    # Patch DB_PATH in research module
    import research
    original_db_path = research.DB_PATH
    research.DB_PATH = str(test_db_path)

    try:
        with get_db() as conn:
            pass

        # Check directory permissions
        dir_mode = os.stat(db_dir).st_mode & 0o777
        assert dir_mode == 0o700, f"Expected directory mode 0700 for existing dir, got {oct(dir_mode)}"

        # Check file permissions
        file_mode = os.stat(str(test_db_path)).st_mode & 0o777
        assert file_mode == 0o600, f"Expected file mode 0600 for existing file, got {oct(file_mode)}"

    finally:
        research.DB_PATH = original_db_path
