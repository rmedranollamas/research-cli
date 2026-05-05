import pytest
from unittest.mock import patch
from research_cli.researcher import ResearchAgent
from research_cli.exceptions import ResearchError


def test_base_url_https_enforcement():
    # After fix, this should raise ResearchError
    agent = ResearchAgent(api_key="fake-key", base_url="http://insecure.example.com")

    with patch("research_cli.researcher.genai.Client"):
        with pytest.raises(ResearchError, match="Insecure base_url"):
            agent.get_client()


def test_base_url_https_success():
    agent = ResearchAgent(api_key="fake-key", base_url="https://secure.example.com")
    with patch("research_cli.researcher.genai.Client") as mock_client:
        client = agent.get_client()
        assert client == mock_client.return_value
        mock_client.assert_called_once()
