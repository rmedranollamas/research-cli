import os
from research_cli import get_db


def test_db_permissions(tmp_path):
    # Use a temporary database path
    test_db_path = tmp_path / "subdir" / "test.db"

    # Patch DB_PATH in research module
    import research_cli

    original_db_path = research_cli.config.DB_PATH
    research_cli.config.DB_PATH = str(test_db_path)

    try:
        with get_db():
            pass

        # Check directory permissions
        db_dir = os.path.dirname(str(test_db_path))
        dir_mode = os.stat(db_dir).st_mode & 0o777
        assert dir_mode == 0o700, f"Expected directory mode 0700, got {oct(dir_mode)}"

        # Check file permissions
        file_mode = os.stat(str(test_db_path)).st_mode & 0o777
        assert file_mode == 0o600, f"Expected file mode 0600, got {oct(file_mode)}"

    finally:
        research_cli.config.DB_PATH = original_db_path


def test_db_permissions_existing(tmp_path):
    # Use a temporary database path
    test_db_path = tmp_path / "existing" / "test.db"
    db_dir = os.path.dirname(str(test_db_path))

    # Pre-create directory and file with loose permissions
    os.makedirs(db_dir, mode=0o777, exist_ok=True)
    os.chmod(db_dir, 0o777)
    # Use sqlite3 to create a valid empty database file
    import sqlite3

    conn = sqlite3.connect(str(test_db_path))
    conn.close()
    os.chmod(test_db_path, 0o666)

    # Patch DB_PATH in research module
    import research_cli

    original_db_path = research_cli.config.DB_PATH
    research_cli.config.DB_PATH = str(test_db_path)

    try:
        with get_db():
            pass

        # Check directory permissions
        dir_mode = os.stat(db_dir).st_mode & 0o777
        assert dir_mode == 0o700, (
            f"Expected directory mode 0700 for existing dir, got {oct(dir_mode)}"
        )

        # Check file permissions
        file_mode = os.stat(str(test_db_path)).st_mode & 0o777
        assert file_mode == 0o600, (
            f"Expected file mode 0600 for existing file, got {oct(file_mode)}"
        )

    finally:
        research_cli.config.DB_PATH = original_db_path
