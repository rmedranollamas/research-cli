import sys
import pytest
from unittest.mock import patch
from research import main, save_task

def test_cli_list_empty(temp_db, capsys):
    """Test 'list' command when no tasks exist."""
    with patch.object(sys, 'argv', ['research', 'list']):
        main()
    
    captured = capsys.readouterr()
    assert "No research tasks found in history." in captured.out

def test_cli_list_with_tasks(temp_db, capsys):
    """Test 'list' command with existing tasks."""
    save_task("how to build a rocket", "model-x")
    
    with patch.object(sys, 'argv', ['research', 'list']):
        main()
    
    captured = capsys.readouterr()
    assert "Recent Research Tasks" in captured.out
    assert "how to build a rocket" in captured.out

def test_cli_show_not_found(temp_db, capsys):
    """Test 'show' command with a non-existent ID."""
    with patch.object(sys, 'argv', ['research', 'show', '999']):
        main()
    
    captured = capsys.readouterr()
    assert "Task 999 not found." in captured.out

def test_cli_show_success(temp_db, capsys):
    """Test 'show' command with an existing ID."""
    from research import update_task
    task_id = save_task("test query", "model-x")
    update_task(task_id, "COMPLETED", report="# Rocket Science\nIt is hard.")
    
    with patch.object(sys, 'argv', ['research', 'show', str(task_id)]):
        main()
    
    captured = capsys.readouterr()
    assert "Research Task " in captured.out
    assert "Rocket Science" in captured.out

