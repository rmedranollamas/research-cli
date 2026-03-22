import asyncio
import pytest
import argparse
from unittest.mock import AsyncMock, MagicMock, patch
from research_cli.cli import handle_run
from research_cli.config import ResearchError

def test_handle_run_no_query():
    # Setup
    agent = MagicMock()
    parser = MagicMock()

    # Mock the subparsers action
    mock_subparsers_action = MagicMock(spec=argparse._SubParsersAction)
    mock_run_parser = MagicMock()
    mock_subparsers_action.choices = {"run": mock_run_parser}
    parser._actions = [mock_subparsers_action]

    args = argparse.Namespace(query=None)

    # Execute
    asyncio.run(handle_run(args, agent, parser))

    # Verify
    mock_run_parser.print_help.assert_called_once()
    agent.run_research.assert_not_called()

def test_handle_run_success():
    # Setup
    agent = MagicMock()
    agent.run_research = AsyncMock(return_value="Report content")
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent="parent-id",
        urls=["url1"],
        files=["file1"],
        use_search=True,
        thinking="medium",
        verbose=True,
        output=None,
        force=False
    )
    parser = MagicMock()

    # Execute
    asyncio.run(handle_run(args, agent, parser))

    # Verify
    agent.run_research.assert_called_once_with(
        "test query",
        "test-model",
        parent_id="parent-id",
        urls=["url1"],
        files=["file1"],
        use_search=True,
        thinking_level="medium",
        verbose=True
    )

def test_handle_run_with_output():
    # Setup
    agent = MagicMock()
    agent.run_research = AsyncMock(return_value="Report content")
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent=None,
        urls=None,
        files=None,
        use_search=True,
        thinking=None,
        verbose=False,
        output="output.md",
        force=True
    )
    parser = MagicMock()

    with patch("research_cli.cli.async_save_report_to_file", new_callable=AsyncMock) as mock_save:
        # Execute
        asyncio.run(handle_run(args, agent, parser))

        # Verify
        agent.run_research.assert_called_once()
        mock_save.assert_called_once_with("Report content", "output.md", True)

def test_handle_run_failure():
    # Setup
    agent = MagicMock()
    agent.run_research = AsyncMock(return_value=None)
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent=None,
        urls=None,
        files=None,
        use_search=True,
        thinking=None,
        verbose=False,
        output=None,
        force=False
    )
    parser = MagicMock()

    # Execute and Verify
    with pytest.raises(ResearchError, match="Research failed"):
        asyncio.run(handle_run(args, agent, parser))

    agent.run_research.assert_called_once()
