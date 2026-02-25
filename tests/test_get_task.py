import pytest
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


@pytest.mark.asyncio
async def test_async_get_task(temp_db):
    """Test retrieving a task asynchronously."""
    query = "Asynchronous test"
    model = "gemini-2.0-flash"
    task_id = save_task(query, model)

    task = await async_get_task(task_id)
    assert task is not None
    assert task[0] == query
    assert task[2] == "PENDING"
