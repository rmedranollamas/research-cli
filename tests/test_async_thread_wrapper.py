import asyncio
import threading
import pytest
from research_cli.utils import async_thread_wrapper

def test_async_thread_wrapper_basic():
    """Test that the wrapper correctly runs a sync function."""
    def sync_func(x, y):
        return x + y

    async_func = async_thread_wrapper(sync_func)

    result = asyncio.run(async_func(1, 2))
    assert result == 3

def test_async_thread_wrapper_args_kwargs():
    """Test that the wrapper correctly passes positional and keyword arguments."""
    def sync_func(a, b, c=0):
        return a * b + c

    async_func = async_thread_wrapper(sync_func)

    result = asyncio.run(async_func(2, 3, c=4))
    assert result == 10

def test_async_thread_wrapper_different_thread():
    """Test that the wrapper runs the function in a different thread."""
    main_thread_id = threading.get_ident()
    thread_ids = []

    def sync_func():
        thread_ids.append(threading.get_ident())
        return "done"

    async_func = async_thread_wrapper(sync_func)

    asyncio.run(async_func())

    assert len(thread_ids) == 1
    assert thread_ids[0] != main_thread_id

def test_async_thread_wrapper_exception():
    """Test that the wrapper propagates exceptions from the sync function."""
    def sync_func():
        raise ValueError("test error")

    async_func = async_thread_wrapper(sync_func)

    with pytest.raises(ValueError, match="test error"):
        asyncio.run(async_func())

def test_async_thread_wrapper_metadata():
    """Test that the wrapper preserves function metadata."""
    def sync_func(a, b):
        """This is a docstring."""
        return a + b

    async_func = async_thread_wrapper(sync_func)

    assert async_func.__name__ == "sync_func"
    assert async_func.__doc__ == "This is a docstring."
