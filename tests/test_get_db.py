import sqlite3
import unittest.mock as mock
import pytest
from research_cli.db import get_db
import research_cli.db as db_module
from research_cli import config

@pytest.fixture(autouse=True)
def reset_db_state():
    """Reset the global _last_db_path before each test."""
    db_module._last_db_path = None
    yield
    db_module._last_db_path = None

def test_get_db_yields_connection_and_closes():
    """Test that get_db yields a connection and closes it."""
    # Set _last_db_path to avoid calling _init_db and its sqlite3.connect call
    db_module._last_db_path = config.DB_PATH

    mock_conn = mock.MagicMock(spec=sqlite3.Connection)
    with mock.patch("sqlite3.connect", return_value=mock_conn) as mock_connect:
        with get_db() as conn:
            assert conn == mock_conn
            mock_connect.assert_called_once_with(config.DB_PATH)

        # Verify close was called
        mock_conn.close.assert_called_once()

def test_get_db_initializes_on_first_call():
    """Test that _init_db is called on the first call to get_db."""
    with mock.patch("research_cli.db._init_db") as mock_init:
        with mock.patch("sqlite3.connect"):
            with get_db():
                pass
            mock_init.assert_called_once_with(config.DB_PATH)
            assert db_module._last_db_path == config.DB_PATH

def test_get_db_does_not_reinitialize_same_path():
    """Test that _init_db is not called if the path hasn't changed."""
    db_module._last_db_path = config.DB_PATH

    with mock.patch("research_cli.db._init_db") as mock_init:
        with mock.patch("sqlite3.connect"):
            with get_db():
                pass
            mock_init.assert_not_called()

def test_get_db_reinitializes_when_path_changes():
    """Test that _init_db is called again if config.DB_PATH changes."""
    db_module._last_db_path = "old_path.db"
    new_path = "new_path.db"

    with mock.patch("research_cli.config.DB_PATH", new_path):
        with mock.patch("research_cli.db._init_db") as mock_init:
            with mock.patch("sqlite3.connect"):
                with get_db():
                    pass
                mock_init.assert_called_once_with(new_path)
                assert db_module._last_db_path == new_path

def test_get_db_lock_usage():
    """Test that the database lock is used during initialization."""
    with mock.patch("research_cli.db._init_db"):
        with mock.patch("sqlite3.connect"):
            with mock.patch.object(db_module, "_db_lock") as mock_lock:
                # Need to mock __enter__ and __exit__ for context manager
                mock_lock.__enter__.return_value = mock_lock

                with get_db():
                    pass

                mock_lock.__enter__.assert_called_once()
                mock_lock.__exit__.assert_called_once()
