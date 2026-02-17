import pytest
import asyncio
from unittest.mock import patch
from research import async_save_task, async_update_task, save_task, get_db

@pytest.mark.asyncio
async def test_async_save_task(temp_db):
    """Test saving a task asynchronously."""
    query = "async query"
    model = "async-model"

    # Test functional correctness
    task_id = await async_save_task(query, model)
    assert task_id is not None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT query, model FROM research_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        assert row[0] == query
        assert row[1] == model

@pytest.mark.asyncio
async def test_async_save_task_calls_save_task():
    """Verify async_save_task calls the synchronous save_task."""
    with patch("research.save_task") as mock_save:
        mock_save.return_value = 123
        result = await async_save_task("q", "m", interaction_id="i", parent_id=None)
        assert result == 123
        mock_save.assert_called_once_with("q", "m", interaction_id="i", parent_id=None)

@pytest.mark.asyncio
async def test_async_update_task(temp_db):
    """Test updating a task asynchronously."""
    task_id = save_task("query", "model")

    # Test update with report
    await async_update_task(task_id, "COMPLETED", report="finished")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, report FROM research_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        assert row[0] == "COMPLETED"
        assert row[1] == "finished"

    # Test update with interaction_id
    await async_update_task(task_id, "IN_PROGRESS", interaction_id="int_async")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, interaction_id FROM research_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        assert row[0] == "IN_PROGRESS"
        assert row[1] == "int_async"

@pytest.mark.asyncio
async def test_async_update_task_calls_update_task():
    """Verify async_update_task calls the synchronous update_task."""
    with patch("research.update_task") as mock_update:
        await async_update_task(456, "ERROR", report="failed", interaction_id="int_123")
        mock_update.assert_called_once_with(456, "ERROR", report="failed", interaction_id="int_123")
