from research_cli import save_task, update_task, get_db


def test_init_db(temp_db):
    """Test that the database is initialized with the correct schema."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check table creation
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_tasks'"
        )
        assert cursor.fetchone() is not None

        # Check index creation
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_research_tasks_created_at'"
        )
        assert cursor.fetchone() is not None


def test_save_task(temp_db):
    """Test saving a new research task."""
    query = "test query"
    model = "test-model"
    task_id = save_task(query, model)

    assert task_id is not None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query, model, status FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == query
        assert row[1] == model
        assert row[2] == "PENDING"


def test_update_task(temp_db):
    """Test updating an existing research task."""
    task_id = save_task("query", "model")

    update_task(task_id, "COMPLETED", report="This is a report")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, report FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "COMPLETED"
        assert row[1] == "This is a report"


def test_update_task_with_interaction_id(temp_db):
    """Test updating task with interaction_id."""
    task_id = save_task("query", "model")
    interaction_id = "int_123"

    update_task(task_id, "IN_PROGRESS", interaction_id=interaction_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, interaction_id FROM research_tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "IN_PROGRESS"
        assert row[1] == interaction_id
