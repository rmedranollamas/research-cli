import os
import asyncio
from .config import QUERY_TRUNCATION_LENGTH

_console = None


def get_console():
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


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
    console.print(Markdown(report))
    console.print("\n" + "=" * 40 + "\n")


def save_report_to_file(
    report: str, output_file: str, force: bool, success_prefix: str = "Report saved to"
):
    console = get_console()
    if os.path.exists(output_file) and not force:
        console.print(
            f"[red]Error: Output file {output_file} already exists. Use --force to overwrite.[/red]"
        )
        return False
    with open(output_file, "w") as f:
        f.write(report)
    console.print(f"[green]{success_prefix} {output_file}[/green]")
    return True


async def async_save_report_to_file(*args, **kwargs):
    return await asyncio.to_thread(save_report_to_file, *args, **kwargs)
