import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from research_cli.researcher import ResearchAgent
from research_cli.config import ResearchError


def test_get_client_success():
    agent = ResearchAgent(api_key="fake-key", base_url="http://fake-url")
    with patch("research_cli.researcher.genai.Client") as mock_client:
        client = agent.get_client(api_version="v1beta", timeout=30)
        assert client == mock_client.return_value
        mock_client.assert_called_once_with(
            api_key="fake-key",
            http_options={
                "api_version": "v1beta",
                "timeout": 30,
                "base_url": "http://fake-url",
            },
        )


def test_get_client_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch("research_cli.researcher.genai.Client", side_effect=Exception("Connection failed")):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            agent.get_client()


def test_get_status_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(
        ResearchAgent,
        "get_client",
        side_effect=ResearchError("Client initialization failed"),
    ):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            asyncio.run(agent.get_status("some-id"))


def test_generate_image_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(
        ResearchAgent,
        "get_client",
        side_effect=ResearchError("Client initialization failed"),
    ):
        with patch("asyncio.to_thread", side_effect=["out.png", ResearchError("Client initialization failed")]):
            with pytest.raises(ResearchError, match="Client initialization failed"):
                asyncio.run(agent.generate_image("prompt", "out.png", "model", False))


def test_run_research_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(
        ResearchAgent,
        "get_client",
        side_effect=ResearchError("Client initialization failed"),
    ):
        with patch("research_cli.researcher.async_save_task", return_value=1):
            with patch.object(agent, "_handle_error") as mock_handle:
                result = asyncio.run(agent.run_research("query", "model"))
                assert result is None
                mock_handle.assert_called_once()


def test_run_search_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(
        ResearchAgent,
        "get_client",
        side_effect=ResearchError("Client initialization failed"),
    ):
        with patch("research_cli.researcher.async_save_task", return_value=1):
            with patch.object(agent, "_handle_error") as mock_handle:
                result = asyncio.run(agent.run_search("query", "model"))
                assert result is None
                mock_handle.assert_called_once()


def test_generate_image_error_handling():
    mock_console = MagicMock()
    agent = ResearchAgent(api_key="fake-key", console=mock_console)
    mock_client = MagicMock()

    error_msg = "Test API Error"
    mock_client.aio.interactions.create.side_effect = Exception(error_msg)

    with patch.object(ResearchAgent, "get_client", return_value=mock_client):
        with patch("asyncio.to_thread", side_effect=["out.png", mock_client]):
            with pytest.raises(ResearchError, match=f"Error generating image: {error_msg}"):
                asyncio.run(agent.generate_image("prompt", "out.png", "model", False))


def test_upload_files_error_handling():
    mock_console = MagicMock()
    agent = ResearchAgent(api_key="fake-key", console=mock_console)
    mock_client = MagicMock()
    error_msg = "Test Upload Error"

    with patch("asyncio.to_thread", side_effect=["test_file.txt", True, Exception(error_msg)]):
        result = asyncio.run(agent._upload_files(mock_client, ["test_file.txt"]))

    assert result == []
    error_printed = False
    for call in mock_console.print.call_args_list:
        args, _ = call
        if len(args) > 0:
            text_obj = args[0]
            if "Error uploading" in str(text_obj) and error_msg in str(text_obj):
                error_printed = True
    assert error_printed


def test_poll_interaction_completed_outputs():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"
    report_parts = ["Part 1"]

    mock_inter = MagicMock()
    mock_inter.status = "COMPLETED"
    mock_inter.outputs = [{"text": "Part 2"}, {"text": "Part 3"}]
    mock_client.aio.interactions.get.return_value = mock_inter

    with patch("asyncio.sleep", return_value=None):
        result = asyncio.run(agent._poll_interaction(
            mock_client, interaction_id, report_parts
        ))

    assert result == "Part 1Part 2Part 3"


def test_poll_interaction_completed_response():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"
    report_parts = []

    mock_inter = MagicMock()
    mock_inter.status = "COMPLETED"
    mock_inter.outputs = []
    mock_inter.response = {"text": "Full Report"}
    mock_client.aio.interactions.get.return_value = mock_inter

    with patch("asyncio.sleep", return_value=None):
        result = asyncio.run(agent._poll_interaction(
            mock_client, interaction_id, report_parts
        ))

    assert result == "Full Report"


def test_poll_interaction_failed():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"

    mock_inter = MagicMock()
    mock_inter.status = "FAILED"
    mock_inter.error = "Some API error"
    mock_client.aio.interactions.get.return_value = mock_inter

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(ResearchError, match="Interaction failed: Some API error"):
            asyncio.run(agent._poll_interaction(mock_client, interaction_id, []))


def test_poll_interaction_cancelled():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"

    mock_inter = MagicMock()
    mock_inter.status = "CANCELLED"
    mock_client.aio.interactions.get.return_value = mock_inter

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(ResearchError, match="Interaction cancelled"):
            asyncio.run(agent._poll_interaction(mock_client, interaction_id, []))


def test_poll_interaction_retry_on_503():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"

    mock_inter = MagicMock()
    mock_inter.status = "COMPLETED"
    mock_inter.outputs = [{"text": "Success after retry"}]

    mock_client.aio.interactions.get.side_effect = [
        Exception("Service Unavailable (503)"),
        mock_inter,
    ]

    with patch("asyncio.sleep", return_value=None):
        result = asyncio.run(agent._poll_interaction(mock_client, interaction_id, []))

    assert result == "Success after retry"
    assert mock_client.aio.interactions.get.call_count == 2


def test_poll_interaction_status_progression():
    agent = ResearchAgent(api_key="fake-key")
    mock_client = MagicMock()
    mock_client.aio.interactions.get = AsyncMock()
    interaction_id = "test-id"

    mock_inter_1 = MagicMock()
    mock_inter_1.status = "IN_PROGRESS"
    mock_inter_2 = MagicMock()
    mock_inter_2.status = "COMPLETED"
    mock_inter_2.outputs = [{"text": "Done"}]

    mock_client.aio.interactions.get.side_effect = [mock_inter_1, mock_inter_2]

    with patch("asyncio.sleep", return_value=None):
        result = asyncio.run(agent._poll_interaction(mock_client, interaction_id, []))

    assert result == "Done"
    assert mock_client.aio.interactions.get.call_count == 2


def test_get_tools_default():
    agent = ResearchAgent(api_key="fake-key")
    with patch("research_cli.researcher.RESEARCH_MCP_SERVERS", []):
        tools = agent._get_tools(use_search=False, urls=None)
        assert tools == []


def test_get_tools_search_and_urls():
    agent = ResearchAgent(api_key="fake-key")
    with patch("research_cli.researcher.RESEARCH_MCP_SERVERS", []):
        tools = agent._get_tools(use_search=True, urls=["http://example.com"])
        assert len(tools) == 2
        assert {"type": "google_search"} in tools
        assert {"type": "url_context"} in tools


def test_get_tools_mcp():
    agent = ResearchAgent(api_key="fake-key")
    mcp_servers = ["http://mcp1.local", "http://mcp2.local"]
    with patch("research_cli.researcher.RESEARCH_MCP_SERVERS", mcp_servers):
        tools = agent._get_tools(use_search=False, urls=None)
        assert len(tools) == 2
        assert tools[0] == {
            "type": "mcp_server",
            "name": "mcp_server_0",
            "url": "http://mcp1.local",
        }
        assert tools[1] == {
            "type": "mcp_server",
            "name": "mcp_server_1",
            "url": "http://mcp2.local",
        }
