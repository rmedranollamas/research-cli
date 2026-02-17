import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from research import run_research, get_db

@pytest.mark.asyncio
async def test_run_research_stream_failure(temp_db, capsys):
    """Test run_research when the stream generation fails during iteration."""
    query = "test failure query"
    model = "deep-research-pro-preview-12-2025"

    # Mock dependencies
    with patch("research.get_api_key", return_value="fake-key"), \
         patch("research.get_gemini_client") as mock_get_client:

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock stream response to raise an exception during iteration
        class AsyncIterError:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise Exception("Stream failure")

        mock_client.aio.interactions.create = AsyncMock(
            return_value=AsyncIterError()
        )

        result = await run_research(query, model)

        assert result is None

        # Verify console output
        captured = capsys.readouterr()
        assert "Error during research:" in captured.out
        assert "Stream failure" in captured.out

        # Verify database state
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, report FROM research_tasks WHERE query = ?", (query,))
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "ERROR"
            assert row[1] == "Research execution failed"

@pytest.mark.asyncio
async def test_run_research_stream_failure_after_interaction(temp_db, capsys):
    """Test run_research when the stream fails after an interaction ID has been received."""
    query = "test failure after interaction"
    model = "deep-research-pro-preview-12-2025"
    interaction_id = "test-inter-id-123"

    # Mock dependencies
    with patch("research.get_api_key", return_value="fake-key"), \
         patch("research.get_gemini_client") as mock_get_client:

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock stream response to yield interaction ID and then fail
        class AsyncIterPartial:
            def __init__(self):
                self.count = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                if self.count == 0:
                    self.count += 1
                    return {"interaction": {"id": interaction_id}}
                raise Exception("Stream failure mid-way")

        mock_client.aio.interactions.create = AsyncMock(
            return_value=AsyncIterPartial()
        )

        result = await run_research(query, model)

        assert result is None

        # Verify console output
        captured = capsys.readouterr()
        assert "Error during research:" in captured.out
        assert "Stream failure mid-way" in captured.out

        # Verify database state
        with get_db() as conn:
            cursor = conn.cursor()
            # Give a small amount of time for background tasks if any (though they might not even finish)
            # but in this case we expect ERROR status to be the final one
            cursor.execute("SELECT status, report, interaction_id FROM research_tasks WHERE query = ?", (query,))
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "ERROR"
            assert row[1] == "Research execution failed"
            assert row[2] == interaction_id
