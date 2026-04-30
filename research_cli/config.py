import os
from research_cli.exceptions import ResearchError

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

_DEFAULT_CONFIG_DIR = os.path.expanduser("~/.research-cli")
CONFIG_DIR = os.getenv("RESEARCH_CONFIG_DIR", _DEFAULT_CONFIG_DIR)

_DOTENV_PATH = os.path.join(CONFIG_DIR, ".env")
if os.path.exists(_DOTENV_PATH):
    try:
        os.chmod(_DOTENV_PATH, 0o600, follow_symlinks=False)
    except (OSError, NotImplementedError):
        pass
    load_dotenv(_DOTENV_PATH)

DB_PATH = os.getenv("RESEARCH_DB_PATH", os.path.join(CONFIG_DIR, "history.db"))
DEFAULT_MODEL = os.getenv("RESEARCH_MODEL", "deep-research-preview-04-2026")
RESEARCH_API_KEY_VAR = "RESEARCH_GEMINI_API_KEY"
RESEARCH_MCP_SERVERS = os.getenv("RESEARCH_MCP_SERVERS", "").split(",")
RESEARCH_MCP_SERVERS = [s.strip() for s in RESEARCH_MCP_SERVERS if s.strip()]
QUERY_TRUNCATION_LENGTH = 50
RECENT_TASKS_LIMIT = 20
POLL_INTERVAL_DEFAULT = 10.0
WORKSPACE_DIR = os.getenv("RESEARCH_WORKSPACE", os.getcwd())
