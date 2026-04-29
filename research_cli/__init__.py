import os
from typing import Optional
from .config import ResearchError as ResearchError
from .utils import get_api_key
from .researcher import ResearchAgent
from .cli import main as main


async def run_research(
    query: str,
    model: str,
    parent_id: Optional[str] = None,
    urls: Optional[list[str]] = None,
    files: Optional[list[str]] = None,
    use_search: bool = True,
    verbose: bool = False,
    plan: bool = False,
    visualization: bool = False,
):
    """Convenience function for running research."""
    api_key = get_api_key()
    base_url = os.getenv("GEMINI_API_BASE_URL")
    agent = ResearchAgent(api_key, base_url=base_url)
    return await agent.run_research(
        query,
        model,
        parent_id=parent_id,
        urls=urls,
        files=files,
        use_search=use_search,
        verbose=verbose,
        collaborative_planning=plan,
        visualization=visualization,
    )


def get_gemini_client():
    """Convenience function to get a Gemini client."""
    api_key = get_api_key()
    base_url = os.getenv("GEMINI_API_BASE_URL")
    agent = ResearchAgent(api_key, base_url=base_url)
    return agent.get_client()
