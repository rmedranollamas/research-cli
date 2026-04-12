
import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
from research_cli.researcher import ResearchAgent

# Test without pytest-asyncio to avoid environment issues
def test_handle_error_traceback_suppression():
    async def run_test():
        mock_console = MagicMock()
        # Mock escape_markup to ensure we test the escaping call regardless of rich availability
        with patch("research_cli.researcher.escape_markup", side_effect=lambda x: x.replace("[", "\\[").replace("]", "\\]")) as mock_escape:
            agent = ResearchAgent(api_key="fake", console=mock_console)

            # Ensure RESEARCH_DEBUG is not set
            with patch.dict(os.environ, {}, clear=True):
                with patch("research_cli.researcher.async_update_task", new_callable=AsyncMock):
                    await agent._handle_error(task_id=1, prefix="Error", db_msg="Sensitive Error Message [bold]markup[/bold]")

            # Check that escape_markup was called
            mock_escape.assert_called_once_with("Sensitive Error Message [bold]markup[/bold]")

            # Check that print_exception was NOT called
            mock_console.print_exception.assert_not_called()

            # Check that error message was printed
            printed_text = ""
            for call in mock_console.print.call_args_list:
                args, _ = call
                if args:
                    printed_text += str(args[0])

            assert "Error:" in printed_text
            assert "Sensitive Error Message \\[bold\\]markup\\[/bold\\]" in printed_text

    asyncio.run(run_test())

def test_handle_error_traceback_enabled():
    async def run_test():
        mock_console = MagicMock()
        agent = ResearchAgent(api_key="fake", console=mock_console)

        # Set RESEARCH_DEBUG to 1
        with patch.dict(os.environ, {"RESEARCH_DEBUG": "1"}):
            with patch("research_cli.researcher.async_update_task", new_callable=AsyncMock):
                await agent._handle_error(task_id=1, prefix="Error", db_msg="Error Message")

        # Check that print_exception WAS called
        mock_console.print_exception.assert_called_once()

    asyncio.run(run_test())
