import pytest
from research_cli.utils import get_console, set_console
from research_cli import get_api_key, ResearchError


def test_mock_console_capsys(capsys):
    set_console(None)
    console = get_console()
    console.print("Hello World")
    captured = capsys.readouterr()
    assert "Hello World" in captured.out


def test_get_api_key_output(capsys, monkeypatch):
    set_console(None)
    monkeypatch.delenv("RESEARCH_GEMINI_API_KEY", raising=False)
    with pytest.raises(ResearchError):
        get_api_key()
    captured = capsys.readouterr()
    assert "RESEARCH_GEMINI_API_KEY environment variable not set." in captured.out
