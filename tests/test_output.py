import os
import sys
import tempfile
import pytest
from unittest.mock import patch, AsyncMock
from research import main, save_task, update_task


def test_run_research_output(temp_db):
    """Test that 'research run' correctly saves output to a file."""
    mock_report = "# Research Report\nThis is a test report."

    with patch("research.run_research", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_report

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_file = tmp.name

        try:
            with patch.object(
                sys,
                "argv",
                ["research", "run", "test query", "--output", output_file, "--force"],
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

    with patch("research.run_research", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_report

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_file = tmp.name
            with open(output_file, "w") as f:
                f.write(existing_content)

        try:
            with patch.object(
                sys, "argv", ["research", "run", "test query", "--output", output_file]
            ):
                main()

            with open(output_file, "r") as f:
                content = f.read()
            assert content == existing_content
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


def test_run_think_output(temp_db):
    """Test that 'research think' correctly saves output to a file."""
    mock_report = "# Thinking Report\nThis is a test response."

    with patch("research.run_think", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_report

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            output_file = tmp.name

        try:
            with patch.object(
                sys,
                "argv",
                ["research", "think", "test query", "--output", output_file, "--force"],
            ):
                main()

            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
            assert content == mock_report
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
