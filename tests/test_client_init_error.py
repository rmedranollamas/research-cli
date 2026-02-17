import pytest
import sqlite3
import os
from unittest.mock import patch, AsyncMock
from research import run_think, run_research, ResearchError, get_db

@pytest.mark.asyncio
async def test_run_think_client_init_error(temp_db, capsys):
    """Test run_think when get_gemini_client fails."""
    with (
        patch("research.get_api_key", return_value="fake-key"),
        patch("google.genai.Client", side_effect=Exception("Init failed")),
    ):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            await run_think("query", "model")

    # Verify DB state
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, report FROM research_tasks WHERE query = 'query'")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "ERROR"
        assert row[1] == "Client initialization failed"

@pytest.mark.asyncio
async def test_run_research_client_init_error(temp_db, capsys):
    """Test run_research when get_gemini_client fails."""
    with (
        patch("research.get_api_key", return_value="fake-key"),
        patch("google.genai.Client", side_effect=Exception("Init failed")),
    ):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            await run_research("query", "model")

    # Verify DB state
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, report FROM research_tasks WHERE query = 'query'")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "ERROR"
        assert row[1] == "Client initialization failed"
