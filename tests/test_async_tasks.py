import pytest
import threading
from unittest.mock import patch, AsyncMock
from research_cli import (
    async_save_task,
    async_update_task,
    save_task,
    update_task,
    get_db,
)


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
        cursor.execute(
            "SELECT query, model FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == query
        assert row[1] == model


@pytest.mark.asyncio
async def test_async_save_task_calls_save_task():
    """Verify async_save_task calls the synchronous save_task."""
    with patch("research_cli.db.save_task") as mock_save:
        mock_save.return_value = 123
        result = await async_save_task("q", "m", interaction_id="i", parent_id=None)
        assert result == 123
        mock_save.assert_called_once_with("q", "m", interaction_id="i", parent_id=None)


@pytest.mark.asyncio
async def test_async_save_task_uses_to_thread():
    """Verify async_save_task specifically uses asyncio.to_thread."""
    with patch(
        "research_cli.db.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = 999
        result = await async_save_task("query", "model", interaction_id="int_1")
        assert result == 999
        mock_to_thread.assert_called_once_with(
            save_task, "query", "model", interaction_id="int_1"
        )


@pytest.mark.asyncio
async def test_async_save_task_runs_in_different_thread():
    """Verify save_task is executed in a separate thread via async_save_task."""
    main_thread_id = threading.get_ident()
    thread_used = None

    def side_effect(*args, **kwargs):
        nonlocal thread_used
        thread_used = threading.get_ident()
        return 42

    with patch("research_cli.db.save_task", side_effect=side_effect):
        await async_save_task("q", "m")

    assert thread_used is not None
    assert thread_used != main_thread_id


@pytest.mark.asyncio
async def test_async_save_task_exception_propagation():
    """Verify exceptions in save_task are propagated by async_save_task."""
    with patch("research_cli.db.save_task", side_effect=ValueError("Test Error")):
        with pytest.raises(ValueError, match="Test Error"):
            await async_save_task("q", "m")


@pytest.mark.asyncio
async def test_async_update_task(temp_db):
    """Test updating a task asynchronously."""
    task_id = save_task("query", "model")

    # Test update with report
    await async_update_task(task_id, "COMPLETED", report="finished")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, report FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "COMPLETED"
        assert row[1] == "finished"

    # Test update with interaction_id
    await async_update_task(task_id, "IN_PROGRESS", interaction_id="int_async")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, interaction_id FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "IN_PROGRESS"
        assert row[1] == "int_async"


@pytest.mark.asyncio
async def test_async_update_task_calls_update_task():
    """Verify async_update_task calls the synchronous update_task."""
    with patch("research_cli.db.update_task") as mock_update:
        await async_update_task(456, "ERROR", report="failed", interaction_id="int_123")
        mock_update.assert_called_once_with(
            456, "ERROR", report="failed", interaction_id="int_123"
        )


@pytest.mark.asyncio
async def test_async_update_task_uses_to_thread():
    """Verify async_update_task specifically uses asyncio.to_thread."""
    with patch(
        "research_cli.db.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        await async_update_task(789, "COMPLETED")
        mock_to_thread.assert_called_once_with(update_task, 789, "COMPLETED")


@pytest.mark.asyncio
async def test_async_update_task_runs_in_different_thread():
    """Verify update_task is executed in a separate thread via async_update_task."""
    main_thread_id = threading.get_ident()
    thread_used = None

    def side_effect(*args, **kwargs):
        nonlocal thread_used
        thread_used = threading.get_ident()

    with patch("research_cli.db.update_task", side_effect=side_effect):
        await async_update_task(123, "IN_PROGRESS")

    assert thread_used is not None
    assert thread_used != main_thread_id


@pytest.mark.asyncio
async def test_async_update_task_exception_propagation():
    """Verify exceptions in update_task are propagated by async_update_task."""
    with patch(
        "research_cli.db.update_task", side_effect=RuntimeError("Update Failed")
    ):
        with pytest.raises(RuntimeError, match="Update Failed"):
            await async_update_task(123, "ERROR")
