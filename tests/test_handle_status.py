import asyncio
import pytest
import argparse
from unittest.mock import AsyncMock, MagicMock, patch
from research_cli.cli import handle_status
from research_cli.config import ResearchError

def test_handle_status_success():
    # Setup
    agent = MagicMock()
    agent.get_status = AsyncMock(return_value="Report content")
    args = argparse.Namespace(interaction_id="test-id", output=None, force=False)

    # Execute
    asyncio.run(handle_status(args, agent))

    # Verify
    agent.get_status.assert_called_once_with("test-id")

def test_handle_status_success_with_output():
    # Setup
    agent = MagicMock()
    agent.get_status = AsyncMock(return_value="Report content")
    args = argparse.Namespace(interaction_id="test-id", output="output.md", force=True)

    with patch("research_cli.cli.async_save_report_to_file", new_callable=AsyncMock) as mock_save:
        # Execute
        asyncio.run(handle_status(args, agent))

        # Verify
        agent.get_status.assert_called_once_with("test-id")
        mock_save.assert_called_once_with("Report content", "output.md", True)

def test_handle_status_failure():
    # Setup
    agent = MagicMock()
    agent.get_status = AsyncMock(return_value=None)
    args = argparse.Namespace(interaction_id="test-id", output=None, force=False)

    # Execute and Verify
    with pytest.raises(ResearchError, match="Status check failed"):
        asyncio.run(handle_status(args, agent))

    agent.get_status.assert_called_once_with("test-id")

def test_handle_status_exception():
    # Setup
    agent = MagicMock()
    agent.get_status = AsyncMock(side_effect=Exception("API Error"))
    args = argparse.Namespace(interaction_id="test-id", output=None, force=False)

    # Execute and Verify
    with pytest.raises(Exception, match="API Error"):
        asyncio.run(handle_status(args, agent))

    agent.get_status.assert_called_once_with("test-id")
