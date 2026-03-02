import os
import asyncio
from .config import (
    QUERY_TRUNCATION_LENGTH,
    WORKSPACE_DIR,
    ResearchError,
    RESEARCH_API_KEY_VAR,
)

_console = None


def get_console():
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


def get_api_key() -> str:
    """Gets the Gemini API key from environment variables or raises ResearchError."""
    api_key = os.getenv(RESEARCH_API_KEY_VAR)
    if not api_key:
        error_message = f"{RESEARCH_API_KEY_VAR} environment variable not set."
        get_console().print(f"[red]Error: {error_message}[/red]")
        raise ResearchError(error_message)
    return api_key


def validate_path(path: str) -> str:
    """
    Validates that the given path is within the WORKSPACE_DIR.
    Returns the resolved real path if valid, otherwise raises ResearchError.
    """
    if not path:
        return path

    abs_workspace = os.path.realpath(WORKSPACE_DIR)

    # If it's a relative path, we consider it relative to WORKSPACE_DIR
    if not os.path.isabs(path):
        abs_path = os.path.realpath(os.path.join(abs_workspace, path))
    else:
        abs_path = os.path.realpath(path)

    # Robust check using commonpath to prevent partial directory matches
    # and ensuring it's within the real workspace directory
    try:
        common = os.path.commonpath([abs_workspace, abs_path])
        if common != abs_workspace:
            raise ResearchError(
                f"Path traversal detected: {path} is outside the workspace {WORKSPACE_DIR}"
            )
    except ValueError:
        # This can happen if paths are on different drives on Windows
        raise ResearchError(
            f"Path traversal detected: {path} is on a different volume than the workspace"
        )

    return abs_path


def truncate_query(query: str) -> str:
    if not query:
        return ""
    return (
        (query[: QUERY_TRUNCATION_LENGTH - 3] + "...")
        if len(query) > QUERY_TRUNCATION_LENGTH
        else query
    )


def get_val(obj, key: str, default=None):
    if obj is None:
        return default
    val = getattr(obj, key, None)
    if val is None and isinstance(obj, dict):
        val = obj.get(key, default)
    return val if val is not None else default


def print_report(report: str):
    from rich.markdown import Markdown

    console = get_console()
    console.print("\n" + "=" * 40 + "\n")
    # For Markdown, rich handles it, but for raw text we use Text(markup=False)
    console.print(Markdown(report))
    console.print("\n" + "=" * 40 + "\n")


def save_report_to_file(
    report: str, output_file: str, force: bool, success_prefix: str = "Report saved to"
):
    console = get_console()
    try:
        output_file = validate_path(output_file)
    except ResearchError as e:
        console.print(f"[red]{e}[/red]")
        return False

    if os.path.exists(output_file) and not force:
        console.print(
            f"[red]Error: Output file {output_file} already exists. Use --force to overwrite.[/red]"
        )
        return False
    with open(output_file, "w") as f:
        f.write(report)
    # Print success message and return True
    console.print(f"[green]{success_prefix} {output_file}[/green]")
    return True


async def async_save_report_to_file(*args, **kwargs):
    return await asyncio.to_thread(save_report_to_file, *args, **kwargs)


def save_binary_to_file(
    data: bytes, output_file: str, force: bool, success_prefix: str = "Binary saved to"
):
    console = get_console()
    try:
        output_file = validate_path(output_file)
    except ResearchError as e:
        console.print(f"[red]{e}[/red]")
        return False

    if os.path.exists(output_file) and not force:
        console.print(
            f"[red]Error: Output file {output_file} already exists. Use --force to overwrite.[/red]"
        )
        return False
    with open(output_file, "wb") as f:
        f.write(data)
    # Print success message and return True
    from rich.text import Text

    console.print(
        Text.assemble(
            (f"{success_prefix} ", "green"),
            (output_file, "bold green"),
        )
    )
    return True


async def async_save_binary_to_file(*args, **kwargs):
    return await asyncio.to_thread(save_binary_to_file, *args, **kwargs)
