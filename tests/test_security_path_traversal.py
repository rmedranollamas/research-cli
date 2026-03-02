import os
import sys
import asyncio
from unittest.mock import MagicMock, patch, mock_open

# Mock dependencies
sys.modules['dotenv'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.progress'] = MagicMock()
sys.modules['rich.text'] = MagicMock()

import pytest
from research_cli.researcher import ResearchAgent
from research_cli.utils import save_report_to_file

@patch('research_cli.researcher.cast', side_effect=lambda t, v: v)
def test_generate_image_path_traversal_vulnerability(mock_cast):
    # Setup
    agent = ResearchAgent("fake-key")
    mock_client = MagicMock()
    agent.get_client = MagicMock(return_value=mock_client)

    # Mock the interaction response
    mock_interaction_dict = {'outputs': [{'type': 'image', 'data': 'dW5pdHRlc3QtZGF0YQ=='}]}

    async def mock_create(**kwargs):
        return mock_interaction_dict

    # Mock the aio.interactions.create call
    mock_client.aio.interactions.create = mock_create

    # Path traversal payload
    traversal_path = "../../tmp/evil.png"

    # We want to check if open is NOT called with the traversal path
    with patch("builtins.open", mock_open()) as mocked_file:
        asyncio.run(agent.generate_image("a prompt", traversal_path, "model-id", force=True))

        # Verify if open was NOT called with the traversal path (because it should be blocked)
        for call in mocked_file.call_args_list:
            assert traversal_path not in call[0]

def test_save_report_path_traversal_vulnerability():
    # Path traversal payload
    traversal_path = "../../tmp/evil_report.txt"
    report_content = "some secret report"

    with patch("builtins.open", mock_open()) as mocked_file:
        save_report_to_file(report_content, traversal_path, force=True)

        # Verify if open was NOT called with the traversal path
        for call in mocked_file.call_args_list:
            assert traversal_path not in call[0]

def test_upload_files_path_traversal_vulnerability():
    agent = ResearchAgent("fake-key")
    mock_client = MagicMock()

    # Path traversal payload
    traversal_path = "../../etc/passwd"

    # We want to check if files.upload is NOT called with the traversal path
    asyncio.run(agent._upload_files(mock_client, [traversal_path]))

    assert not mock_client.files.upload.called
