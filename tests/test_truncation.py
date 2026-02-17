import sys
from unittest.mock import patch
from research_cli import truncate_query, QUERY_TRUNCATION_LENGTH, save_task, main


def test_truncate_query_short():
    """Test that queries shorter than the truncation length are not truncated."""
    query = "Short query"
    assert truncate_query(query) == query


def test_truncate_query_exact():
    """Test that queries exactly at the truncation length are not truncated."""
    query = "a" * QUERY_TRUNCATION_LENGTH
    assert truncate_query(query) == query


def test_truncate_query_long():
    """Test that queries longer than the truncation length are truncated."""
    long_query = "a" * (QUERY_TRUNCATION_LENGTH + 10)
    expected = "a" * (QUERY_TRUNCATION_LENGTH - 3) + "..."
    assert truncate_query(long_query) == expected


def test_truncate_query_plus_one():
    """Test that a query with length QUERY_TRUNCATION_LENGTH + 1 is truncated."""
    query = "a" * (QUERY_TRUNCATION_LENGTH + 1)
    expected = "a" * (QUERY_TRUNCATION_LENGTH - 3) + "..."
    assert truncate_query(query) == expected


def test_truncate_query_none():
    """Test handling of None input."""
    assert truncate_query(None) == ""


def test_truncate_query_empty():
    """Test handling of empty string."""
    assert truncate_query("") == ""


def test_cli_list_query_truncation(temp_db, capsys):
    """Test that long queries are truncated in the list view (integrated test)."""
    long_query = "b" * (QUERY_TRUNCATION_LENGTH + 10)
    save_task(long_query, "model-x")

    with patch.object(sys, "argv", ["research", "list"]):
        main()

    captured = capsys.readouterr()
    expected_display = "b" * (QUERY_TRUNCATION_LENGTH - 3) + "..."
    assert expected_display in captured.out
    assert long_query not in captured.out
