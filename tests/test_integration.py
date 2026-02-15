import pytest
import os
from research import run_research, get_db


@pytest.mark.asyncio
async def test_run_research_full_flow(temp_db, fake_server):
    """Test the full research flow from creation to completion using the fake server."""
    query = "Tell me about quantum computing"
    model = "test-model"

    report = await run_research(query, model)

    assert report is not None
    assert "Finished content" in report

    # Verify database state
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, report, interaction_id FROM research_tasks WHERE query = ?",
            (query,),
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "COMPLETED"
        assert "Finished content" in row[1]


@pytest.mark.asyncio
async def test_run_research_polling_fallback(temp_db, fake_server):
    """Test that the CLI correctly falls back to polling if the stream ends early."""
    os.environ["RESEARCH_POLL_INTERVAL"] = "1"
    query = "This is a slow query"
    model = "test-model"

    # The fake server will end the stream without content for this query
    report = await run_research(query, model)

    assert report is not None
    assert "Finished content" in report

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM research_tasks WHERE query = ?", (query,))
        assert cursor.fetchone()[0] == "COMPLETED"

    del os.environ["RESEARCH_POLL_INTERVAL"]
