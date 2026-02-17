import pytest
import os
import sys
import sqlite3
from unittest.mock import patch
from research_cli import (
    get_api_key,
    run_think,
    run_research,
    ResearchError,
    main,
    get_gemini_client,
)


def test_get_api_key_missing(capsys):
    """Test get_api_key when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with pytest.raises(
            ResearchError, match="GEMINI_API_KEY environment variable not set."
        ):
            get_api_key()

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out


def test_get_api_key_empty(capsys):
    """Test get_api_key when GEMINI_API_KEY is an empty string."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        with pytest.raises(
            ResearchError, match="GEMINI_API_KEY environment variable not set."
        ):
            get_api_key()

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out


def test_get_api_key_success():
    """Test get_api_key when GEMINI_API_KEY is present."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        assert get_api_key() == "test-key"


def test_get_gemini_client_no_api_key():
    """Test get_gemini_client when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with pytest.raises(
            ResearchError, match="GEMINI_API_KEY environment variable not set."
        ):
            get_gemini_client()


@pytest.mark.asyncio
async def test_run_think_no_api_key(temp_db, capsys):
    """Test run_think when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with pytest.raises(
            ResearchError, match="GEMINI_API_KEY environment variable not set."
        ):
            await run_think("query", "model")

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out

    # Verify no task was saved
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM research_tasks")
        assert cursor.fetchone()[0] == 0


def test_cli_think_no_api_key(temp_db, capsys):
    """Test CLI think command when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with patch.object(sys, "argv", ["research", "think", "query"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out


@pytest.mark.asyncio
async def test_run_research_no_api_key(temp_db, capsys):
    """Test run_research when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with pytest.raises(
            ResearchError, match="GEMINI_API_KEY environment variable not set."
        ):
            await run_research("query", "model")

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out

    # Verify no task was saved
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM research_tasks")
        assert cursor.fetchone()[0] == 0


def test_cli_run_no_api_key(temp_db, capsys):
    """Test CLI run command when GEMINI_API_KEY is missing."""
    with patch.dict(os.environ):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with patch.object(sys, "argv", ["research", "run", "query"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Error: GEMINI_API_KEY environment variable not set." in captured.out
