import os
from typing import TYPE_CHECKING, Optional
from .cli import main as main
from .researcher import ResearchAgent as ResearchAgent
from .db import (
    get_db as get_db,
    save_task as save_task,
    update_task as update_task,
    async_save_task as async_save_task,
    async_update_task as async_update_task,
    get_recent_tasks as get_recent_tasks,
    async_get_recent_tasks as async_get_recent_tasks,
    get_task as get_task,
    async_get_task as async_get_task,
    init_db as init_db,
)
from .utils import (
    truncate_query as truncate_query,
    get_val as get_val,
    get_console,
    print_report as print_report,
    save_report_to_file as save_report_to_file,
    async_save_report_to_file as async_save_report_to_file,
)
from .config import (
    ResearchError as ResearchError,
    QUERY_TRUNCATION_LENGTH as QUERY_TRUNCATION_LENGTH,
    DB_PATH as DB_PATH,
    RESEARCH_API_KEY_VAR as RESEARCH_API_KEY_VAR,
)

if TYPE_CHECKING:
    from google import genai


def get_api_key() -> str:
    """Gets the Gemini API key from environment variables or raises ResearchError."""
    api_key = os.getenv(RESEARCH_API_KEY_VAR)
    if not api_key:
        get_console().print(
            f"[red]Error: {RESEARCH_API_KEY_VAR} environment variable not set.[/red]"
        )
        raise ResearchError(f"{RESEARCH_API_KEY_VAR} environment variable not set.")
    return api_key


def get_gemini_client(
    api_key: Optional[str] = None,
    api_version: str = "v1alpha",
    timeout: Optional[int] = None,
) -> "genai.Client":
    if api_key is None:
        api_key = get_api_key()
    agent = ResearchAgent(api_key, os.getenv("GEMINI_API_BASE_URL"))
    return agent.get_client(api_version=api_version, timeout=timeout)


# For backward compatibility with tests that expect run_research at top level
async def run_research(*args, **kwargs):
    api_key = get_api_key()
    agent = ResearchAgent(api_key, os.getenv("GEMINI_API_BASE_URL"))
    return await agent.run_research(*args, **kwargs)
