import pytest
import os
from unittest.mock import patch, MagicMock
from research_cli.researcher import ResearchAgent
from research_cli.config import ResearchError

def test_get_client_success():
    agent = ResearchAgent(api_key="fake-key", base_url="http://fake-url")
    with patch("google.genai.Client") as mock_client:
        client = agent.get_client(api_version="v1beta", timeout=30)
        assert client == mock_client.return_value
        mock_client.assert_called_once_with(
            api_key="fake-key",
            http_options={"api_version": "v1beta", "timeout": 30, "base_url": "http://fake-url"}
        )

def test_get_client_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch("google.genai.Client", side_effect=Exception("Connection failed")):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            agent.get_client()

@pytest.mark.asyncio
async def test_get_status_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(ResearchAgent, "get_client", side_effect=ResearchError("Client initialization failed")):
        with pytest.raises(ResearchError, match="Client initialization failed"):
            await agent.get_status("some-id")

@pytest.mark.asyncio
async def test_generate_image_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    with patch.object(ResearchAgent, "get_client", side_effect=ResearchError("Client initialization failed")):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(ResearchError, match="Client initialization failed"):
                await agent.generate_image("prompt", "out.png", "model", False)

@pytest.mark.asyncio
async def test_run_research_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    # Both run_research and _run_interaction try to get a client.
    # In run_research, it's used for file uploads first.
    with patch.object(ResearchAgent, "get_client", side_effect=ResearchError("Client initialization failed")):
        with patch("research_cli.researcher.async_save_task", return_value=1):
            with patch.object(agent, "_handle_error") as mock_handle:
                with pytest.raises(ResearchError, match="Client initialization failed"):
                    await agent.run_research("query", "model")
                # Should be called once by run_research
                mock_handle.assert_called_once()

@pytest.mark.asyncio
async def test_run_search_client_init_failure():
    agent = ResearchAgent(api_key="fake-key")
    # run_search calls _run_interaction which calls get_client
    with patch.object(ResearchAgent, "get_client", side_effect=ResearchError("Client initialization failed")):
        with patch("research_cli.researcher.async_save_task", return_value=1):
            with patch.object(agent, "_handle_error") as mock_handle:
                with pytest.raises(ResearchError, match="Client initialization failed"):
                    await agent.run_search("query", "model")
                # Should be called once by _run_interaction
                mock_handle.assert_called_once()
