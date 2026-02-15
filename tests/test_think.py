import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from research import main

def test_cli_think_help(capsys):
    """Test 'think' command help."""
    with patch.object(sys, 'argv', ['research', 'think', '--help']):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "Start a new thinking task" in captured.out

def test_cli_think_no_query(capsys):
    """Test 'think' command without query."""
    with patch.object(sys, 'argv', ['research', 'think']):
        main()

    captured = capsys.readouterr()
    assert "usage: research think" in captured.out

@patch('research.save_task', return_value=1)
@patch('research.update_task')
@patch('google.genai.Client')
def test_cli_think_success(mock_client_class, mock_update, mock_save, temp_db, capsys):
    """Test 'think' command success."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock stream response
    chunk1 = MagicMock()
    chunk1.candidates = [MagicMock()]
    chunk1.candidates[0].content.parts = [MagicMock(thought=True, text="Thinking...")]

    chunk2 = MagicMock()
    chunk2.candidates = [MagicMock()]
    chunk2.candidates[0].content.parts = [MagicMock(thought=False, text="The answer is 42")]

    mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

    with patch.dict('os.environ', {'GEMINI_API_KEY': 'fake-key'}), \
         patch.object(sys, 'argv', ['research', 'think', 'what is the meaning of life', '--timeout', '60']):
        main()

    # Verify client was initialized with correct timeout
    args, kwargs = mock_client_class.call_args
    assert kwargs['http_options']['timeout'] == 60

    captured = capsys.readouterr()
    assert "Gemini Deep Think Starting" in captured.out
    assert "Thinking..." in captured.out
    assert "The answer is 42" in captured.out

    # Verify DB updates
    assert mock_save.called
    mock_update.assert_any_call(1, "COMPLETED", "The answer is 42")

@patch('research.run_think')
def test_cli_think_direct_entry(mock_run_think):
    """Test direct script entry for 'think'."""
    with patch.object(sys, 'argv', ['think', 'hello']):
        main()

    # Check that it was called with 'hello' and the default model
    args, kwargs = mock_run_think.call_args
    assert args[0] == 'hello'
    assert args[1] == 'gemini-2.0-flash-thinking-exp'
