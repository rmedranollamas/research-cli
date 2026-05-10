import pytest
import asyncio
import base64
import os
from unittest.mock import patch, MagicMock, AsyncMock
from research_cli.researcher import ResearchAgent
from research_cli.config import WORKSPACE_DIR

def test_handle_inline_image_success():
    agent = ResearchAgent(api_key="fake-key")
    agent.console = MagicMock()

    base64_data = "ZmFrZSBkYXRh" # "fake data"
    task_id = 1
    decoded_bytes = b"fake data"

    # Mocking:
    # 1. asyncio.to_thread for base64.b64decode
    # 2. time.time()
    # 3. async_save_binary_to_file

    with patch("asyncio.to_thread", AsyncMock(return_value=decoded_bytes)) as mock_to_thread, \
         patch("time.time", return_value=1234567.89), \
         patch("research_cli.researcher.async_save_binary_to_file", AsyncMock(return_value=True)) as mock_save:

        asyncio.run(agent._handle_inline_image(base64_data, task_id))

        # Verify asyncio.to_thread was called for decoding
        mock_to_thread.assert_called_once_with(base64.b64decode, base64_data)

        # Verify async_save_binary_to_file was called with correct arguments
        expected_timestamp = 1234567890
        expected_filename = f"research_task_{task_id}_{expected_timestamp}.png"
        expected_path = os.path.join(WORKSPACE_DIR, expected_filename)

        mock_save.assert_called_once_with(
            decoded_bytes,
            expected_path,
            force=True,
            success_prefix="Visualization saved to"
        )

def test_handle_inline_image_failure():
    agent = ResearchAgent(api_key="fake-key")
    agent.console = MagicMock()

    base64_data = "invalid-base64"
    task_id = 1

    # Simulate exception in decoding
    error_msg = "Decoding failed"
    with patch("asyncio.to_thread", AsyncMock(side_effect=Exception(error_msg))):
        asyncio.run(agent._handle_inline_image(base64_data, task_id))

        # Verify console.print was called with error message
        agent.console.print.assert_called_once()
        args, _ = agent.console.print.call_args
        assert f"[yellow]Failed to save inline image: {error_msg}[/yellow]" in args[0]
