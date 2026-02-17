import os
import importlib
from unittest.mock import patch


def test_dotenv_current_dir_not_loaded(tmp_path):
    """
    Test that a .env file in the current directory is not automatically loaded.
    """
    # Create a dummy .env in a temporary directory
    env_file = tmp_path / ".env"
    env_file.write_text("MALICIOUS_VAR=true")

    # Change current working directory to the temporary directory
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Clear environment variable if it exists
        if "MALICIOUS_VAR" in os.environ:
            del os.environ["MALICIOUS_VAR"]

        # Reload the research module to trigger load_dotenv
        import research_cli.config

        importlib.reload(research_cli.config)

        # Verify if it's currently loaded
        assert os.getenv("MALICIOUS_VAR") is None
    finally:
        os.chdir(old_cwd)


def test_dotenv_config_dir_loaded(tmp_path):
    """
    Test that a .env file in the designated config directory is loaded.
    """
    # Create a dummy .env in a temporary directory acting as config dir
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    env_file = config_dir / ".env"
    env_file.write_text("SECURE_VAR=true")

    with patch.dict(os.environ, {"RESEARCH_CONFIG_DIR": str(config_dir)}):
        # Clear environment variable if it exists
        if "SECURE_VAR" in os.environ:
            del os.environ["SECURE_VAR"]

        # Reload the research module
        import research_cli.config

        importlib.reload(research_cli.config)

        # Verify it IS loaded
        assert os.getenv("SECURE_VAR") == "true"
