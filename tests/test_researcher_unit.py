import pytest
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

@pytest.mark.asyncio
async def test_generate_image_error_handling():
    # Setup mock console
    mock_console = MagicMock()

    agent = ResearchAgent(api_key="fake-key", console=mock_console)
    mock_client = MagicMock()

    # Mock create to raise an Exception
    # Need to simulate client.aio.interactions.create raising an error
    error_msg = "Test API Error"
    mock_client.aio.interactions.create.side_effect = Exception(error_msg)

    with patch.object(ResearchAgent, "get_client", return_value=mock_client):
        with patch("research_cli.utils.validate_path", return_value="out.png"):
            with patch("os.path.exists", return_value=False):
                await agent.generate_image("prompt", "out.png", "model", False)

    # Verify that console.print and console.print_exception were called
    assert mock_console.print.called

    # We should get 1 print for the Text object representing the error message
    # Let's verify that the error message contains the expected string
    error_printed = False
    for call in mock_console.print.call_args_list:
        args, kwargs = call
        if len(args) > 0:
            text_obj = args[0]

            if hasattr(text_obj, "plain") and "Error generating image:" in text_obj.plain and error_msg in text_obj.plain:
                error_printed = True
            elif hasattr(text_obj, "markup") and "Error generating image:" in text_obj.markup and error_msg in text_obj.markup:
                error_printed = True
            elif str(text_obj) == f"Error generating image: {error_msg}":
                 error_printed = True

    assert error_printed, "The error message should have been printed to the console."
    assert mock_console.print_exception.called, "console.print_exception should have been called."

@pytest.mark.asyncio
async def test_upload_files_error_handling():
    mock_console = MagicMock()
    agent = ResearchAgent(api_key="fake-key", console=mock_console)
    mock_client = MagicMock()

    error_msg = "Test Upload Error"

    with patch("research_cli.researcher.validate_path", return_value="test_file.txt"):
        with patch("os.path.exists", return_value=True):
            with patch("asyncio.to_thread", side_effect=Exception(error_msg)):
                result = await agent._upload_files(mock_client, ["test_file.txt"])

    assert result == []

    error_printed = False
    for call in mock_console.print.call_args_list:
        args, kwargs = call
        if len(args) > 0:
            text_obj = args[0]
            if hasattr(text_obj, "plain") and "Error uploading" in text_obj.plain and error_msg in text_obj.plain:
                error_printed = True
            elif hasattr(text_obj, "markup") and "Error uploading" in text_obj.markup and error_msg in text_obj.markup:
                error_printed = True
            elif f"Error uploading test_file.txt: {error_msg}" in str(text_obj):
                error_printed = True

    assert error_printed, "The error message should have been printed to the console."
