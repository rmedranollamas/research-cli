import asyncio
import pytest
import argparse
from unittest.mock import AsyncMock, MagicMock, patch
from research_cli.cli import handle_search
from research_cli.config import ResearchError

def test_handle_search_no_query():
    # Setup
    agent = MagicMock()
    parser = MagicMock()

    # Mock the subparsers action
    mock_subparsers_action = MagicMock(spec=argparse._SubParsersAction)
    mock_search_parser = MagicMock()
    mock_subparsers_action.choices = {"search": mock_search_parser}
    parser._actions = [mock_subparsers_action]

    args = argparse.Namespace(query=None)

    # Execute
    asyncio.run(handle_search(args, agent, parser))

    # Verify
    mock_search_parser.print_help.assert_called_once()
    agent.run_search.assert_not_called()

def test_handle_search_success():
    # Setup
    agent = MagicMock()
    agent.run_search = AsyncMock(return_value="Search content")
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent="parent-id",
        verbose=True,
        output=None,
        force=False
    )
    parser = MagicMock()

    # Execute
    asyncio.run(handle_search(args, agent, parser))

    # Verify
    agent.run_search.assert_called_once_with(
        "test query",
        "test-model",
        parent_id="parent-id",
        verbose=True
    )

def test_handle_search_with_output():
    # Setup
    agent = MagicMock()
    agent.run_search = AsyncMock(return_value="Search content")
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent="parent-id",
        verbose=False,
        output="search_output.md",
        force=True
    )
    parser = MagicMock()

    with patch("research_cli.cli.async_save_report_to_file", new_callable=AsyncMock) as mock_save:
        # Execute
        asyncio.run(handle_search(args, agent, parser))

        # Verify
        agent.run_search.assert_called_once_with(
            "test query",
            "test-model",
            parent_id="parent-id",
            verbose=False
        )
        mock_save.assert_called_once_with("Search content", "search_output.md", True)

def test_handle_search_failure():
    # Setup
    agent = MagicMock()
    agent.run_search = AsyncMock(return_value=None)
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent=None,
        verbose=False,
        output="wont_save.md",
        force=False
    )
    parser = MagicMock()

    with patch("research_cli.cli.async_save_report_to_file", new_callable=AsyncMock) as mock_save:
        # Execute and Verify
        with pytest.raises(ResearchError, match="Search failed"):
            asyncio.run(handle_search(args, agent, parser))

        agent.run_search.assert_called_once()
        mock_save.assert_not_called()

def test_handle_search_exception():
    # Setup
    agent = MagicMock()
    agent.run_search = AsyncMock(side_effect=ResearchError("API Error"))
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent=None,
        verbose=False,
        output=None,
        force=False
    )
    parser = MagicMock()

    # Execute and Verify
    with pytest.raises(ResearchError, match="API Error"):
        asyncio.run(handle_search(args, agent, parser))

    agent.run_search.assert_called_once()

def test_handle_search_success_no_save():
    # Setup
    agent = MagicMock()
    agent.run_search = AsyncMock(return_value="Search content")
    args = argparse.Namespace(
        query="test query",
        model="test-model",
        parent=None,
        verbose=False,
        output=None,
        force=False
    )
    parser = MagicMock()

    with patch("research_cli.cli.async_save_report_to_file", new_callable=AsyncMock) as mock_save:
        # Execute
        asyncio.run(handle_search(args, agent, parser))

        # Verify
        agent.run_search.assert_called_once()
        mock_save.assert_not_called()
