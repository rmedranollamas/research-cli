import pytest
import sys
from unittest.mock import patch
from research_cli import run_research, main
from research_cli.db import get_db


@pytest.mark.asyncio
async def test_run_research_client_init_error(temp_db, capsys):
    """Test run_research when get_gemini_client fails."""
    with (
        patch("research_cli.get_api_key", return_value="fake-key"),
        patch("google.genai.Client", side_effect=Exception("Init failed")),
    ):
        # run_research now catches the ResearchError from get_client, handles it, and returns None
        result = await run_research("query", "model")
        assert result is None

    # Verify console output
    captured = capsys.readouterr()
    assert "Error initializing Gemini client:" in captured.out
    assert "Exception occurred" in captured.out

    # Verify DB state
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, report FROM research_tasks WHERE query = 'query'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "ERROR"
        # Updated message format
        assert (
            "Client initialization failed: Client initialization failed: Init failed"
            in row[1]
        )


def test_cli_run_client_init_error(temp_db, capsys):
    """Test CLI 'run' command when client initialization fails."""
    with (
        patch("research_cli.get_api_key", return_value="fake-key"),
        patch("google.genai.Client", side_effect=Exception("Init failed")),
        patch.object(sys, "argv", ["research", "run", "test query"]),
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Error initializing Gemini client:" in captured.out
    assert "Exception occurred" in captured.out

    # Verify DB state
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, report FROM research_tasks WHERE query = 'test query'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "ERROR"
        assert (
            "Client initialization failed: Client initialization failed: Init failed"
            in row[1]
        )
