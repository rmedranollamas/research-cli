import pytest
import os
import sys
import sqlite3
from unittest.mock import patch
from research_cli import (
    get_api_key,
    run_research,
    main,
    get_gemini_client,
)
from research_cli.config import ResearchError, RESEARCH_API_KEY_VAR


def test_get_api_key_missing(capsys):
    """Test get_api_key when API key is missing."""
    with patch.dict(os.environ):
        if RESEARCH_API_KEY_VAR in os.environ:
            del os.environ[RESEARCH_API_KEY_VAR]
        with pytest.raises(
            ResearchError, match=f"{RESEARCH_API_KEY_VAR} environment variable not set."
        ):
            get_api_key()

    captured = capsys.readouterr()
    assert (
        f"Error: {RESEARCH_API_KEY_VAR} environment variable not set." in captured.out
    )


def test_get_api_key_empty(capsys):
    """Test get_api_key when API key is an empty string."""
    with patch.dict(os.environ, {RESEARCH_API_KEY_VAR: ""}):
        with pytest.raises(
            ResearchError, match=f"{RESEARCH_API_KEY_VAR} environment variable not set."
        ):
            get_api_key()

    captured = capsys.readouterr()
    assert (
        f"Error: {RESEARCH_API_KEY_VAR} environment variable not set." in captured.out
    )


def test_get_api_key_success():
    """Test get_api_key when API key is present."""
    with patch.dict(os.environ, {RESEARCH_API_KEY_VAR: "test-key"}):
        assert get_api_key() == "test-key"


def test_get_gemini_client_no_api_key():
    """Test get_gemini_client when API key is missing."""
    with patch.dict(os.environ):
        if RESEARCH_API_KEY_VAR in os.environ:
            del os.environ[RESEARCH_API_KEY_VAR]
        with pytest.raises(
            ResearchError, match=f"{RESEARCH_API_KEY_VAR} environment variable not set."
        ):
            get_gemini_client()


def test_get_gemini_client_success():
    """Test get_gemini_client success path."""
    with patch.dict(
        os.environ,
        {
            RESEARCH_API_KEY_VAR: "test-key",
            "GEMINI_API_BASE_URL": "https://test-api.example.com",
        },
    ):
        with patch("research_cli.researcher.genai.Client") as mock_client:
            client = get_gemini_client()
            assert client == mock_client.return_value
            mock_client.assert_called_once_with(
                api_key="test-key",
                http_options={
                    "api_version": "v1alpha",
                    "base_url": "https://test-api.example.com",
                },
            )


def test_run_research_no_api_key(temp_db, capsys):
    """Test run_research when API key is missing."""
    import asyncio
    with patch.dict(os.environ):
        if RESEARCH_API_KEY_VAR in os.environ:
            del os.environ[RESEARCH_API_KEY_VAR]
        with pytest.raises(
            ResearchError, match=f"{RESEARCH_API_KEY_VAR} environment variable not set."
        ):
            asyncio.run(run_research("query", "model"))

    captured = capsys.readouterr()
    assert (
        f"Error: {RESEARCH_API_KEY_VAR} environment variable not set." in captured.out
    )

    # Verify no task was saved
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM research_tasks")
        assert cursor.fetchone()[0] == 0


def test_cli_run_no_api_key(temp_db, capsys):
    """Test CLI run command when API key is missing."""
    with patch.dict(os.environ):
        if RESEARCH_API_KEY_VAR in os.environ:
            del os.environ[RESEARCH_API_KEY_VAR]
        with patch.object(sys, "argv", ["research", "run", "query"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert (
        f"Error: {RESEARCH_API_KEY_VAR} environment variable not set." in captured.out
    )
