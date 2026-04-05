import pytest
import asyncio
import sqlite3
from unittest.mock import patch
from research_cli.db import save_task, update_task, get_task, async_get_task


def test_get_task_success(temp_db):
    """Test retrieving a task successfully."""
    query = "What is the capital of France?"
    model = "gemini-2.0-flash"
    task_id = save_task(query, model)

    # Initially report should be None and status PENDING
    task = get_task(task_id)
    assert task is not None
    assert task[0] == query
    assert task[1] is None
    assert task[2] == "PENDING"

    # Update the task
    report = "The capital of France is Paris."
    status = "COMPLETED"
    update_task(task_id, status, report)

    # Retrieve again
    task = get_task(task_id)
    assert task is not None
    assert task[0] == query
    assert task[1] == report
    assert task[2] == status


def test_get_task_not_found(temp_db):
    """Test retrieving a non-existent task."""
    task = get_task(999)
    assert task is None


def test_async_get_task(temp_db):
    """Test retrieving a task asynchronously."""
    query = "Asynchronous test"
    model = "gemini-2.0-flash"
    task_id = save_task(query, model)

    task = asyncio.run(async_get_task(task_id))
    assert task is not None
    assert task[0] == query
    assert task[2] == "PENDING"


def test_get_task_error(temp_db):
    """Test get_task handles database errors gracefully."""
    with patch("sqlite3.connect", side_effect=sqlite3.Error("DB connection error")):
        # We need to bypass the _last_db_path check or force a re-init if get_db calls it
        # Actually, get_db calls sqlite3.connect(config.DB_PATH)
        task = get_task(1)
        assert task is None


def test_get_task_invalid_id(temp_db):
    """Test get_task with invalid ID types."""
    # SQLite often handles types loosely, but let's see how it behaves
    assert get_task(None) is None
    assert get_task("invalid") is None
    assert get_task(-1) is None
