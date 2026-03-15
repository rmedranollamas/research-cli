import os
import importlib
import pytest
from unittest.mock import patch

def test_dotenv_permissions_enforced(tmp_path):
    """
    Test that the .env file permissions are enforced to 0600.
    """
    # Create a dummy .env with loose permissions
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    env_file = config_dir / ".env"
    env_file.write_text("VAR=val")
    os.chmod(env_file, 0o666)

    # Ensure it's 0666 (or at least not 0600)
    # Note: on some filesystems/OSes, 0666 might be adjusted by umask,
    # but 0666 is generally more permissive than 0600.
    initial_mode = os.stat(env_file).st_mode & 0o777
    assert initial_mode != 0o600

    with patch.dict(os.environ, {"RESEARCH_CONFIG_DIR": str(config_dir)}):
        # Reload the research module to trigger the permission enforcement
        import research_cli.config
        importlib.reload(research_cli.config)

        # Check permissions
        final_mode = os.stat(env_file).st_mode & 0o777
        assert final_mode == 0o600
