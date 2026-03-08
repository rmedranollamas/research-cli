import os
from .config import (
    DEFAULT_MODEL as DEFAULT_MODEL,
    ResearchError as ResearchError,
    RESEARCH_API_KEY_VAR as RESEARCH_API_KEY_VAR,
)
from .db import (
    init_db as init_db,
    save_task as save_task,
    update_task as update_task,
    get_task as get_task,
    get_recent_tasks as get_recent_tasks,
)
from .utils import (
    get_api_key as get_api_key,
    truncate_query as truncate_query,
    get_val as get_val,
    get_console as get_console,
    print_report as print_report,
    save_report_to_file as save_report_to_file,
    save_binary_to_file as save_binary_to_file,
)
from .researcher import ResearchAgent as ResearchAgent
from .cli import main as main


async def run_research(query: str, model: str):
    """Convenience function for running research."""
    api_key = get_api_key()
    base_url = os.getenv("GEMINI_API_BASE_URL")
    agent = ResearchAgent(api_key, base_url=base_url)
    return await agent.run_research(query, model)


def get_gemini_client():
    """Convenience function to get a Gemini client."""
    api_key = get_api_key()
    base_url = os.getenv("GEMINI_API_BASE_URL")
    agent = ResearchAgent(api_key, base_url=base_url)
    return agent.get_client()
