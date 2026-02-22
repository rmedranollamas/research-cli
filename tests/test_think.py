import pytest
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from research_cli import main


def test_cli_think_help(capsys):
    """Test 'think' command help."""
    with patch.object(sys, "argv", ["research", "think", "--help"]):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "Start a new thinking task" in captured.out


def test_cli_think_no_query(capsys):
    """Test 'think' command without query."""
    with patch.object(sys, "argv", ["research", "think"]):
        main()

    captured = capsys.readouterr()
    assert "usage: research think" in captured.out


@patch("research_cli.db.save_task", return_value=1)
@patch("research_cli.db.update_task")
@patch("research_cli.researcher.ResearchAgent.get_client")
def test_cli_think_success(mock_get_client, mock_update, mock_save, temp_db, capsys):
    """Test 'think' command success."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock stream response
    chunk1 = MagicMock()
    chunk1.candidates = [MagicMock()]
    chunk1.candidates[0].content.parts = [MagicMock(thought=True, text="Thinking...")]

    chunk2 = MagicMock()
    chunk2.candidates = [MagicMock()]
    chunk2.candidates[0].content.parts = [
        MagicMock(thought=False, text="The answer is 42")
    ]

    async def async_iter():
        yield chunk1
        yield chunk2

    mock_client.aio.models.generate_content_stream = AsyncMock(
        return_value=async_iter()
    )

    with (
        patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}),
        patch.object(
            sys,
            "argv",
            ["research", "think", "what is the meaning of life", "--timeout", "60"],
        ),
    ):
        main()

    # Verify client was initialized with correct timeout and api_version
    args, kwargs = mock_get_client.call_args
    assert kwargs["timeout"] == 60
    assert kwargs["api_version"] == "v1alpha"

    captured = capsys.readouterr()
    assert "Gemini Deep Think Starting" in captured.out
    assert "Thinking..." in captured.out
    assert "The answer is 42" in captured.out

    # Verify DB updates
    assert mock_save.called
    mock_update.assert_any_call(1, "COMPLETED", "The answer is 42")


@patch("research_cli.researcher.ResearchAgent.run_think")
def test_cli_think_direct_entry(mock_run_think):
    """Test direct script entry for 'think'."""
    with (
        patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}),
        patch.object(sys, "argv", ["think", "hello"]),
    ):
        main()

    # Check that it was called with 'hello' and the default model
    args, kwargs = mock_run_think.call_args
    assert args[0] == "hello"
    assert args[1] == "gemini-2.0-flash-thinking-exp"
