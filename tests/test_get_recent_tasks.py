import pytest
from research_cli import get_recent_tasks, async_get_recent_tasks, get_db, save_task

def test_get_recent_tasks_empty(temp_db):
    """Test that it returns an empty list when no tasks exist."""
    tasks = get_recent_tasks(10)
    assert tasks == []

def test_get_recent_tasks_limit(temp_db):
    """Test that it returns the correct number of tasks when limit is applied."""
    for i in range(5):
        save_task(f"query {i}", "model")

    tasks = get_recent_tasks(3)
    assert len(tasks) == 3

def test_get_recent_tasks_order(temp_db):
    """Test that it returns tasks in descending order of created_at."""
    # Manually insert tasks with specific timestamps to ensure order
    with get_db() as conn:
        conn.execute(
            "INSERT INTO research_tasks (query, model, created_at) VALUES (?, ?, ?)",
            ("query 1", "model", "2023-01-01 10:00:00")
        )
        conn.execute(
            "INSERT INTO research_tasks (query, model, created_at) VALUES (?, ?, ?)",
            ("query 2", "model", "2023-01-01 11:00:00")
        )
        conn.execute(
            "INSERT INTO research_tasks (query, model, created_at) VALUES (?, ?, ?)",
            ("query 3", "model", "2023-01-01 09:00:00")
        )
        conn.commit()

    tasks = get_recent_tasks(10)
    assert len(tasks) == 3
    # Should be in order: query 2 (11:00), query 1 (10:00), query 3 (09:00)
    assert tasks[0][1] == "query 2"
    assert tasks[1][1] == "query 1"
    assert tasks[2][1] == "query 3"

def test_get_recent_tasks_all(temp_db):
    """Test that it returns all tasks when limit is greater than the total number of tasks."""
    for i in range(3):
        save_task(f"query {i}", "model")

    tasks = get_recent_tasks(10)
    assert len(tasks) == 3

@pytest.mark.asyncio
async def test_async_get_recent_tasks(temp_db):
    """Test that the asynchronous version works as expected."""
    for i in range(3):
        save_task(f"query {i}", "model")

    tasks = await async_get_recent_tasks(10)
    assert len(tasks) == 3
