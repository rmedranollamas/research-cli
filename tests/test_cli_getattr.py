import pytest
from unittest.mock import patch
from research_cli import cli

def test_getattr_version():
    """Test that accessing VERSION triggers __getattr__ and calls get_version."""
    with patch("research_cli.cli.get_version", return_value="test-version") as mock_get_version:
        # Accessing cli.VERSION should trigger __getattr__ which calls get_version
        assert cli.VERSION == "test-version"
        mock_get_version.assert_called_once()

def test_getattr_invalid_attribute():
    """Test that accessing a non-existent attribute raises AttributeError."""
    with pytest.raises(AttributeError) as excinfo:
        _ = cli.NON_EXISTENT_ATTRIBUTE

    assert "module 'research_cli.cli' has no attribute 'NON_EXISTENT_ATTRIBUTE'" in str(excinfo.value)
