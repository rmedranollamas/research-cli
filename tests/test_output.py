import os
import sys
import tempfile
import pytest
from unittest.mock import patch, AsyncMock
from research_cli import main
from research_cli.db import save_task, update_task


def test_run_research_output(temp_db):
    """Test that 'research run' correctly saves output to a file."""
    mock_report = "# Research Report\nThis is a test report."

    with patch(
        "research_cli.researcher.ResearchAgent.run_research", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = mock_report

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_file = tmp.name

        try:
            # Mock WORKSPACE_DIR to allow saving to the temp file
            with patch(
                "research_cli.utils.WORKSPACE_DIR", os.path.dirname(output_file)
            ):
                with patch.object(
                    sys,
                    "argv",
                    [
                        "research",
                        "run",
                        "test query",
                        "--output",
                        output_file,
                        "--force",
                    ],
                ):
                    main()

                assert os.path.exists(output_file)
                with open(output_file, "r") as f:
                    content = f.read()
                assert content == mock_report
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


def test_run_research_no_overwrite(temp_db):
    """Test that 'research run' fails when output file exists and --force is not used."""
    mock_report = "# New Report"
    existing_content = "original content"

    with patch(
        "research_cli.researcher.ResearchAgent.run_research", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = mock_report

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_file = tmp.name
            with open(output_file, "w") as f:
                f.write(existing_content)

        try:
            with patch(
                "research_cli.utils.WORKSPACE_DIR", os.path.dirname(output_file)
            ):
                with patch.object(
                    sys,
                    "argv",
                    ["research", "run", "test query", "--output", output_file],
                ):
                    with pytest.raises(SystemExit) as excinfo:
                        main()
                    assert excinfo.value.code == 1

                with open(output_file, "r") as f:
                    content = f.read()
                assert content == existing_content
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


def test_show_task_output(temp_db):
    """Test that 'research show' correctly saves output to a file."""
    query = "test query"
    mock_report = "# Saved Report\nContent from DB."
    task_id = save_task(query, "model-x")
    update_task(task_id, "COMPLETED", report=mock_report)

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        output_file = tmp.name

    try:
        with patch("research_cli.utils.WORKSPACE_DIR", os.path.dirname(output_file)):
            with patch.object(
                sys,
                "argv",
                ["research", "show", str(task_id), "--output", output_file, "--force"],
            ):
                main()

            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
            assert content == mock_report
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
