import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from research_cli import run_think


@pytest.mark.asyncio
async def test_run_think_stream_failure(capsys):
    """Test run_think when the stream generation fails."""
    # Mock dependencies
    with (
        patch("research_cli.get_api_key", return_value="fake-key"),
        patch("research_cli.researcher.ResearchAgent.get_client") as mock_get_client,
        patch(
            "research_cli.researcher.async_save_task", new_callable=AsyncMock
        ) as mock_async_save,
        patch(
            "research_cli.researcher.async_update_task", new_callable=AsyncMock
        ) as mock_async_update,
    ):
        mock_async_save.return_value = 1

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock stream response to raise an exception during iteration
        class AsyncIterError:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise Exception("Stream failure")

        mock_client.aio.models.generate_content_stream = AsyncMock(
            return_value=AsyncIterError()
        )

        result = await run_think("test query", "gemini-2.0-flash-thinking-exp")

        assert result is None
        # Verify task was updated to ERROR
        mock_async_update.assert_called_with(
            1, "ERROR", "Execution failed", interaction_id=None
        )

        captured = capsys.readouterr()
        assert "Error during thinking:" in captured.out
        assert "Stream failure" in captured.out
