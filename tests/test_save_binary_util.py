import pytest
import os
from research_cli.utils import save_binary_to_file, async_save_binary_to_file

def test_save_binary_to_file_success(tmp_path):
    data = b"binary data"
    output_file = tmp_path / "test.bin"
    result = save_binary_to_file(data, str(output_file), force=False)
    assert result is True
    assert output_file.exists()
    assert output_file.read_bytes() == data

def test_save_binary_to_file_exists_no_force(tmp_path):
    data = b"new data"
    existing = b"old data"
    output_file = tmp_path / "test.bin"
    output_file.write_bytes(existing)
    result = save_binary_to_file(data, str(output_file), force=False)
    assert result is False
    assert output_file.read_bytes() == existing

@pytest.mark.asyncio
async def test_async_save_binary_to_file(tmp_path):
    data = b"async binary data"
    output_file = tmp_path / "async_test.bin"
    result = await async_save_binary_to_file(data, str(output_file), force=False)
    assert result is True
    assert output_file.exists()
    assert output_file.read_bytes() == data
