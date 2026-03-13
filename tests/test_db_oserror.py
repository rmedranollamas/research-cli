import os
import unittest.mock as mock
import sqlite3
from research_cli.db import _init_db

def test_init_db_dir_chmod_oserror(tmp_path):
    """Test that _init_db handles OSError when chmod-ing the database directory."""
    test_db_path = tmp_path / "dir_error" / "test.db"
    db_dir = str(test_db_path.parent)
    os.makedirs(db_dir, exist_ok=True)

    # Ensure is_owner will be true in the test
    # By default, files created in tmp_path will be owned by the current user

    with mock.patch("os.chmod") as mock_chmod:
        # Side effect: raise OSError only when the path is db_dir
        def side_effect(path, mode):
            if path == db_dir:
                raise OSError("Mocked chmod directory error")
            return None

        mock_chmod.side_effect = side_effect

        # This should not raise exception
        _init_db(str(test_db_path))

        # Verify chmod was indeed called for the directory
        # (It might be called for the file too, depending on execution flow)
        mock_chmod.assert_any_call(db_dir, 0o700)

    # Verify the database was initialized anyway (schema created)
    with sqlite3.connect(str(test_db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_tasks'"
        )
        assert cursor.fetchone() is not None

def test_init_db_file_chmod_oserror(tmp_path):
    """Test that _init_db handles OSError when chmod-ing the database file."""
    test_db_path = str(tmp_path / "file_error.db")

    with mock.patch("os.chmod") as mock_chmod:
        # Side effect: raise OSError only when the path is test_db_path
        def side_effect(path, mode):
            if path == test_db_path:
                raise OSError("Mocked chmod file error")
            return None

        mock_chmod.side_effect = side_effect

        # This should not raise exception
        _init_db(test_db_path)

        # Verify chmod was called for the file
        mock_chmod.assert_any_call(test_db_path, 0o600)

    # Verify the database was initialized anyway
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_tasks'"
        )
        assert cursor.fetchone() is not None
