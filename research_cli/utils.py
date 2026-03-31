import os
import asyncio
from typing import Union, Optional, Any
from .config import (
    QUERY_TRUNCATION_LENGTH,
    WORKSPACE_DIR,
    ResearchError,
    RESEARCH_API_KEY_VAR,
)

_console: Optional[Any] = None


def get_console() -> Any:
    """Returns the singleton rich console instance."""
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


def set_console(console: Any):
    """Sets a custom console (useful for testing)."""
    global _console
    _console = console


def get_api_key() -> str:
    """
    Gets the Gemini API key from environment variables or raises ResearchError.

    Returns:
        The API key string.

    Raises:
        ResearchError: If the API key is not found in the environment.
    """
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

    Args:
        path: The path to validate.

    Returns:
        The resolved absolute path.

    Raises:
        ResearchError: If the path is invalid or points outside the workspace.
    """
    if not path:
        raise ResearchError("Empty or invalid path provided")

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
    """Truncates the query to a safe length for display."""
    if not query:
        return ""
    return (
        (query[: QUERY_TRUNCATION_LENGTH - 3] + "...")
        if len(query) > QUERY_TRUNCATION_LENGTH
        else query
    )


def get_val(obj: Any, key: str, default: Any = None) -> Any:
    """
    Safely retrieves a value from an object or dictionary.

    Args:
        obj: The object or dictionary to retrieve from.
        key: The key or attribute name.
        default: The default value to return if not found.

    Returns:
        The retrieved value or the default.
    """
    if obj is None:
        return default
    val = getattr(obj, key, None)
    if val is None and isinstance(obj, dict):
        val = obj.get(key, default)
    return val if val is not None else default


def print_report(report: str):
    """Prints a research report formatted as Markdown."""
    from rich.markdown import Markdown

    console = get_console()
    console.print("\n" + "=" * 40 + "\n")
    console.print(Markdown(report))
    console.print("\n" + "=" * 40 + "\n")


def escape_markup(text: str) -> str:
    """Safely escapes rich markup, handling missing dependency gracefully."""
    try:
        from rich.markup import escape
        return escape(text)
    except (ImportError, ModuleNotFoundError):
        return text


def _save_to_file(
    data: Union[str, bytes],
    output_file: str,
    force: bool,
    success_prefix: str,
    binary: bool = False,
) -> bool:
    """Internal helper to save data to a file with path validation."""
    console = get_console()

    try:
        output_file = validate_path(output_file)
    except ResearchError as e:
        console.print(f"[red]{escape_markup(str(e))}[/red]")
        return False

    flags = os.O_WRONLY | os.O_CREAT
    if force:
        flags |= os.O_TRUNC
        # O_NOFOLLOW prevents following symlinks for the last component.
        # This is a security hardening to ensure we are not tricked into
        # overwriting a file via a symlink created after path validation.
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
    else:
        flags |= os.O_EXCL

    try:
        fd = os.open(output_file, flags)
        with os.fdopen(fd, "wb" if binary else "w") as f:
            f.write(data)
    except FileExistsError:
        console.print(
            f"[red]Error: Output file {escape_markup(output_file)} already exists. Use --force to overwrite.[/red]"
        )
        return False
    except OSError as e:
        import errno
        if hasattr(errno, "ELOOP") and e.errno == errno.ELOOP:
            console.print(
                f"[red]Error: {escape_markup(output_file)} is a symlink. Overwriting symlinks is disallowed for security.[/red]"
            )
        else:
            console.print(f"[red]Error saving to file {escape_markup(output_file)}: {escape_markup(str(e))}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error saving to file {escape_markup(output_file)}: {escape_markup(str(e))}[/red]")
        return False

    from rich.text import Text

    console.print(
        Text.assemble(
            (f"{success_prefix} ", "green"),
            (output_file, "bold green"),
        )
    )
    return True


def save_report_to_file(
    report: str,
    output_file: str,
    force: bool,
    success_prefix: str = "Report saved to",
) -> bool:
    """Saves a research report to a text file."""
    return _save_to_file(report, output_file, force, success_prefix, binary=False)


async def async_save_report_to_file(*args, **kwargs) -> bool:
    """Asynchronous wrapper for save_report_to_file."""
    return await asyncio.to_thread(save_report_to_file, *args, **kwargs)


def save_binary_to_file(
    data: bytes,
    output_file: str,
    force: bool,
    success_prefix: str = "Binary saved to",
) -> bool:
    """Saves binary data (e.g., an image) to a file."""
    return _save_to_file(data, output_file, force, success_prefix, binary=True)


async def async_save_binary_to_file(*args, **kwargs) -> bool:
    """Asynchronous wrapper for save_binary_to_file."""
    return await asyncio.to_thread(save_binary_to_file, *args, **kwargs)
