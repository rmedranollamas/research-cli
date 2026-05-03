import asyncio
import pytest
import argparse
from unittest.mock import AsyncMock, MagicMock
from research_cli.cli import handle_generate_image
from research_cli.exceptions import ResearchError

def test_handle_generate_image_success():
    # Setup
    agent = MagicMock()
    agent.generate_image = AsyncMock()
    args = argparse.Namespace(
        prompt="a cute robot",
        output="robot.png",
        model="gemini-3-pro-image-preview",
        force=False
    )

    # Execute
    asyncio.run(handle_generate_image(args, agent))

    # Verify
    agent.generate_image.assert_called_once_with(
        "a cute robot", "robot.png", "gemini-3-pro-image-preview", False
    )

def test_handle_generate_image_research_error():
    # Setup
    agent = MagicMock()
    agent.generate_image = AsyncMock(side_effect=ResearchError("Client initialization failed"))
    args = argparse.Namespace(
        prompt="a cute robot",
        output="robot.png",
        model="gemini-3-pro-image-preview",
        force=False
    )

    # Execute and Verify
    with pytest.raises(ResearchError, match="Client initialization failed"):
        asyncio.run(handle_generate_image(args, agent))

    agent.generate_image.assert_called_once_with(
        "a cute robot", "robot.png", "gemini-3-pro-image-preview", False
    )
