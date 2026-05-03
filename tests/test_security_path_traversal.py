from unittest.mock import MagicMock, patch, mock_open
import pytest
from research_cli.researcher import ResearchAgent
from research_cli.utils import save_report_to_file


def test_generate_image_path_traversal_vulnerability():
    import asyncio
    # Setup
    agent = ResearchAgent("fake-key")
    mock_client = MagicMock()

    # Mock get_client to return our mock_client
    with patch.object(ResearchAgent, "get_client", return_value=mock_client):
        # Mock the interaction response
        mock_interaction_dict = {
            "outputs": [{"type": "image", "data": "dW5pdHRlc3QtZGF0YQ=="}]
        }

        async def mock_create(**kwargs):
            return mock_interaction_dict

        # Mock the aio.interactions.create call
        mock_client.aio.interactions.create = mock_create

        # Path traversal payload
        traversal_path = "../../tmp/evil.png"

        # The vulnerability should be caught by validate_path and raise ResearchError
        from research_cli.exceptions import ResearchError

        with pytest.raises(ResearchError, match="Path traversal detected"):
            asyncio.run(agent.generate_image(
                "a prompt", traversal_path, "model-id", force=True
            ))


def test_save_report_path_traversal_vulnerability():
    # Path traversal payload
    traversal_path = "../../tmp/evil_report.txt"
    report_content = "some secret report"

    with patch("builtins.open", mock_open()) as mocked_file:
        save_report_to_file(report_content, traversal_path, force=True)

        # Verify if open was NOT called with the traversal path
        for call in mocked_file.call_args_list:
            if call[0]:
                assert traversal_path not in call[0][0]


def test_upload_files_path_traversal_vulnerability():
    import asyncio
    agent = ResearchAgent("fake-key")
    mock_client = MagicMock()

    # Path traversal payload
    traversal_path = "../../etc/passwd"

    # We want to check if files.upload is NOT called with the traversal path
    # validate_path should catch it and _upload_single_file will return None
    uris = asyncio.run(agent._upload_files(mock_client, [traversal_path]))

    # Verify that upload was NOT called and result is empty
    assert uris == []
    assert not mock_client.files.upload.called
