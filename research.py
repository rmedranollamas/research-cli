import os
import sys
import asyncio
import argparse
import sqlite3
import threading
from contextlib import contextmanager
from typing import List, Optional, TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from google import genai


# Custom exception for research errors
class ResearchError(Exception):
    """Custom exception for research-related errors."""

    pass


# Load environment variables from .env if present
load_dotenv()

# Configuration Constants
DB_PATH = os.getenv(
    "RESEARCH_DB_PATH", os.path.expanduser("~/.research-cli/history.db")
)
DB_DIR = os.path.dirname(DB_PATH)
DEFAULT_MODEL = os.getenv("RESEARCH_MODEL", "deep-research-pro-preview-12-2025")
DEFAULT_THINK_MODEL = os.getenv("THINK_MODEL", "gemini-2.0-flash-thinking-exp")
QUERY_TRUNCATION_LENGTH = 50

RECENT_TASKS_LIMIT = 20


def truncate_query(query: str) -> str:
    """Truncates a query for display if it exceeds QUERY_TRUNCATION_LENGTH."""
    if query is None:
        return ""
    return (
        (query[: QUERY_TRUNCATION_LENGTH - 3] + "...")
        if len(query) > QUERY_TRUNCATION_LENGTH
        else query
    )


# Global Rich console placeholder
_console = None


def get_console():
    """Returns a globally shared Rich console, initializing it on first use."""
    global _console
    if _console is None:
        from rich.console import Console

        _console = Console()
    return _console


# Database initialization state
_db_lock = threading.Lock()
_last_db_path: Optional[str] = None


def get_val(obj, key: str, default=None):
    """Safely gets a value from an object or dictionary."""
    if obj is None:
        return default
    val = getattr(obj, key, None)
    if val is None and isinstance(obj, dict):
        val = obj.get(key, default)
    return val if val is not None else default


_last_db_path: Optional[str] = None


@contextmanager
def get_db():
    """Provides a thread-safe database connection with lazy initialization."""
    global _last_db_path

    # Lazy initialization with double-checked locking
    if _last_db_path != DB_PATH:
        with _db_lock:
            if _last_db_path != DB_PATH:
                _init_db(DB_PATH)
                _last_db_path = DB_PATH

    conn = sqlite3.connect(DB_PATH)
    if _last_db_path != DB_PATH:
        _init_db(conn)
        _last_db_path = DB_PATH
    try:
        yield conn
    finally:
        conn.close()


def _init_db(db_path: str):
    """Internal helper to initialize the database filesystem and schema."""
    db_dir = os.path.dirname(db_path)
    # Set restrictive umask (only user can read/write)
    old_umask = os.umask(0o077)
    try:
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o700, exist_ok=True)
        else:
            # Ensure existing directory has correct permissions if it's likely our own app dir
            # Avoid chmod'ing system or shared directories like /tmp
            try:
                st = os.stat(db_dir)
                # Only chmod if we own it and it's not a system directory
                # os.getuid is available on Unix
                is_owner = hasattr(os, "getuid") and st.st_uid == os.getuid()
                if is_owner and db_dir not in ["/tmp", "/var/tmp", "/"]:
                    os.chmod(db_dir, 0o700)
            except OSError:
                pass

        with sqlite3.connect(db_path) as conn:
            # Ensure database file has correct permissions
            try:
                os.chmod(db_path, 0o600)
            except OSError:
                pass
            _init_db_schema(conn)
    finally:
        os.umask(old_umask)


def _init_db_schema(conn: sqlite3.Connection):
    """Internal helper to initialize the database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id TEXT UNIQUE, parent_id TEXT,
            query TEXT,
            model TEXT,
            status TEXT,
            report TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at ON research_tasks (created_at)"
    )
    conn.commit()


def init_db():
    """Explicitly initializes the database. Now handled lazily by get_db()."""
    with get_db():
        pass


def save_task(
    query: str,
    model: str,
    interaction_id: Optional[str] = None,
    parent_id: Optional[str] = None,
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO research_tasks (query, model, interaction_id, status, parent_id) VALUES (?, ?, ?, ?, ?)",
            (query, model, interaction_id, "PENDING", parent_id),
        )
        task_id = cursor.lastrowid
        conn.commit()
        return task_id


async def async_save_task(*args, **kwargs):
    """Asynchronous wrapper for save_task."""
    return await asyncio.to_thread(save_task, *args, **kwargs)


def update_task(
    task_id: int,
    status: str,
    report: Optional[str] = None,
    interaction_id: Optional[str] = None,
):
    with get_db() as conn:
        if interaction_id:
            conn.execute(
                "UPDATE research_tasks SET status = ?, report = ?, interaction_id = ? WHERE id = ?",
                (status, report, interaction_id, task_id),
            )
        else:
            conn.execute(
                "UPDATE research_tasks SET status = ?, report = ? WHERE id = ?",
                (status, report, task_id),
            )
        conn.commit()


async def async_update_task(*args, **kwargs):
    """Asynchronous wrapper for update_task."""
    return await asyncio.to_thread(update_task, *args, **kwargs)


def get_api_key() -> str:
    """Gets the Gemini API key from environment variables or raises ResearchError."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        get_console().print(
            "[red]Error: GEMINI_API_KEY environment variable not set.[/red]"
        )
        raise ResearchError("GEMINI_API_KEY environment variable not set.")
    return api_key


def get_gemini_client(
    api_key: Optional[str] = None,
    api_version: str = "v1alpha",
    timeout: Optional[int] = None,
) -> "genai.Client":
    """Helper to initialize the Gemini client with common configuration."""
    from google import genai

    if api_key is None:
        api_key = get_api_key()

    http_options = {"api_version": api_version}
    if timeout is not None:
        http_options["timeout"] = timeout

    base_url = os.getenv("GEMINI_API_BASE_URL")
    if base_url:
        http_options["base_url"] = base_url

    return genai.Client(api_key=api_key, http_options=http_options)


async def run_research(query: str, model_id: str, parent_id: Optional[str] = None):
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown

    api_key = get_api_key()
    console = get_console()

    task_id = await async_save_task(query, model_id, parent_id=parent_id)

    try:
        client = get_gemini_client(api_key=api_key)
    except Exception:
        console.print("[red]Error initializing Gemini client:[/red]")
        console.print_exception()
        await async_update_task(task_id, "ERROR", "Client initialization failed")
        raise ResearchError("Client initialization failed")

    console.print(
        Panel(
            f"[bold blue]Query:[/bold blue] {query}\n[bold blue]Model:[/bold blue] {model_id}",
            title="Deep Research Starting",
        )
    )

    try:
        stream = client.interactions.create(
            agent=model_id,
            input=query,
            background=True,
            stream=True,
            agent_config={"type": "deep-research", "thinking_summaries": "auto"},
            previous_interaction_id=parent_id,
        )

        report_parts: List[str] = []
        interaction_id = None
        background_tasks = set()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing...", total=None)

            for event in stream:
                inter = get_val(event, "interaction")
                if inter and not interaction_id:
                    interaction_id = get_val(inter, "id")

                    if interaction_id:
                        update_job = asyncio.create_task(
                            async_update_task(
                                task_id, "IN_PROGRESS", interaction_id=interaction_id
                            )
                        )
                        background_tasks.add(update_job)
                        update_job.add_done_callback(background_tasks.discard)
                        progress.update(
                            task, description=f"Researching (ID: {interaction_id})..."
                        )

                thought = get_val(event, "thought")
                if thought:
                    progress.update(
                        task, description=f"[italic grey]{thought}[/italic grey]"
                    )
                    console.print(f"[italic grey]> {thought}[/italic grey]")

                content = get_val(event, "content")
                if content:
                    parts = get_val(content, "parts", [])
                    for part in parts:
                        text = get_val(part, "text")
                        if text:
                            report_parts.append(text)

            progress.update(task, description="Stream finished.", completed=True)

        # Wait for any background database updates to finish
        if background_tasks:
            results = await asyncio.gather(*background_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    console.print(
                        f"[yellow]Warning: A background database update failed: {result}[/yellow]"
                    )

        report_content = "".join(report_parts)

        if not report_content and interaction_id:
            console.print(
                f"[yellow]Stream ended without report. Polling interaction {interaction_id}...[/yellow]"
            )
            last_status = None
            while True:
                final_inter = client.interactions.get(id=interaction_id)
                status = get_val(final_inter, "status", "UNKNOWN").upper()
                if status != last_status:
                    console.print(f"[dim]Current status: {status}[/dim]")
                    last_status = status

                if status == "COMPLETED":
                    outputs = get_val(final_inter, "outputs", [])
                    for output in outputs:
                        text = get_val(output, "text")
                        if text:
                            report_parts.append(text)

                    if not report_parts:
                        response = get_val(final_inter, "response")
                        if response:
                            text = get_val(response, "text")
                            if text:
                                report_parts.append(text)
                    break
                elif status in ["FAILED", "CANCELLED"]:
                    break

                poll_interval = int(os.getenv("RESEARCH_POLL_INTERVAL", "10"))
                await asyncio.sleep(poll_interval)

            report_content = "".join(report_parts)

    except Exception:
        console.print("[red]Error during research:[/red]")
        console.print_exception()
        await async_update_task(task_id, "ERROR", "Research execution failed")
        return None

    if report_content:
        await async_update_task(task_id, "COMPLETED", report_content)
        console.print("\n" + "=" * 40 + "\n")
        console.print(Markdown(report_content))
        console.print("\n" + "=" * 40 + "\n")

        return report_content
    else:
        await async_update_task(task_id, "FAILED")
        console.print("[yellow]No report content received.[/yellow]")
        return None


async def run_research_cmd(args):
    console = get_console()
    parent_id = args.parent
    report = await run_research(args.query, args.model, parent_id=parent_id)
    if report and args.output:
        if os.path.exists(args.output) and not args.force:
            console.print(
                f"[red]Error: Output file {args.output} already exists. Use --force to overwrite.[/red]"
            )
            return
        with open(args.output, "w") as f:
            f.write(report)
        console.print(f"[green]Report saved to {args.output}[/green]")


async def run_think(
    query: str, model_id: str, api_version: str = "v1alpha", timeout: int = 1800
):
    from google.genai import types
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown

    api_key = get_api_key()
    console = get_console()

    task_id = await async_save_task(query, model_id)

    try:
        client = get_gemini_client(
            api_key=api_key, api_version=api_version, timeout=timeout
        )
    except Exception:
        console.print("[red]Error initializing Gemini client:[/red]")
        console.print_exception()
        await async_update_task(task_id, "ERROR", "Client initialization failed")
        raise ResearchError("Client initialization failed")

    console.print(
        Panel(
            f"[bold blue]Query:[/bold blue] {query}\n[bold blue]Model:[/bold blue] {model_id}\n[bold blue]API Version:[/bold blue] {api_version}",
            title="Gemini Deep Think Starting",
        )
    )

    try:
        # Flash Thinking model handles thoughts via GenerateContentConfig
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        )

        stream = client.models.generate_content_stream(
            model=model_id,
            contents=query,
            config=config,
        )

        report_parts: List[str] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Deep Think processing...", total=None)
            console.print("[italic grey]Thinking...[/italic grey]")
            for chunk in stream:
                for part in chunk.candidates[0].content.parts:
                    if part.thought:
                        console.print(
                            f"[italic grey]{part.text}[/italic grey]",
                            end="",
                            highlight=False,
                        )
                    elif part.text:
                        report_parts.append(part.text)

            console.print("\n[green]Finished thinking.[/green]")

        report_content = "".join(report_parts)

    except Exception:
        console.print("[red]Error during thinking:[/red]")
        console.print_exception()
        await async_update_task(task_id, "ERROR", "Execution failed")
        return None

    if report_content:
        await async_update_task(task_id, "COMPLETED", report_content)
        console.print("\n" + "=" * 40 + "\n")
        console.print(Markdown(report_content))
        console.print("\n" + "=" * 40 + "\n")

        return report_content
    else:
        await async_update_task(task_id, "FAILED")
        console.print("[yellow]No content received.[/yellow]")
        return None


async def run_think_cmd(args):
    console = get_console()
    report = await run_think(
        args.query, args.model, api_version=args.api_version, timeout=args.timeout
    )
    if report and args.output:
        if os.path.exists(args.output) and not args.force:
            console.print(
                f"[red]Error: Output file {args.output} already exists. Use --force to overwrite.[/red]"
            )
            return
        with open(args.output, "w") as f:
            f.write(report)
        console.print(f"[green]Saved to {args.output}[/green]")


def show_task(task_id: int, output_file: Optional[str] = None, force: bool = False):
    from rich.panel import Panel
    from rich.markdown import Markdown

    console = get_console()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query, report, status FROM research_tasks WHERE id = ?", (task_id,)
        )
        task = cursor.fetchone()

    if not task:
        console.print(f"[red]Task {task_id} not found.[/red]")
        return

    query, report, status = task
    console.print(
        Panel(
            f"[bold blue]Query:[/bold blue] {query}\n[bold blue]Status:[/bold blue] {status}",
            title=f"Research Task {task_id}",
        )
    )
    if report:
        console.print("\n" + "=" * 40 + "\n")
        console.print(Markdown(report))
        console.print("\n" + "=" * 40 + "\n")

        if output_file:
            if os.path.exists(output_file) and not force:
                console.print(
                    f"[red]Error: Output file {output_file} already exists. Use --force to overwrite.[/red]"
                )
                return
            with open(output_file, "w") as f:
                f.write(report)
            console.print(f"[green]Report saved to {output_file}[/green]")
    else:
        console.print("[yellow]No report content available for this task.[/yellow]")


def list_tasks():
    from rich.table import Table

    console = get_console()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, query, status, created_at, interaction_id FROM research_tasks ORDER BY created_at DESC LIMIT {RECENT_TASKS_LIMIT}"
        )
        tasks = cursor.fetchall()

    if not tasks:
        console.print("[yellow]No research tasks found in history.[/yellow]")
        return

    table = Table(title="Recent Research Tasks")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Query", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created At", style="magenta")
    table.add_column("Interaction ID", style="dim")

    for task_id, query, status, created_at, inter_id in tasks:
        # Truncate query for display
        display_query = truncate_query(query)
        table.add_row(str(task_id), display_query, status, created_at, inter_id or "-")

    console.print(table)


def main():
    # Check if called as 'think' script
    script_name = os.path.basename(sys.argv[0])

    # If called via 'think' entry point, we want to default to the 'think' subcommand
    if script_name == "think":
        if len(sys.argv) > 1 and sys.argv[1] not in [
            "run",
            "think",
            "list",
            "show",
            "-h",
            "--help",
            "--version",
        ]:
            sys.argv.insert(1, "think")

    parser = argparse.ArgumentParser(description="Gemini Deep Research CLI")
    parser.add_argument("--version", action="version", version="research-cli 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Start a new research task")
    run_parser.add_argument("query", nargs="?", help="The research query")
    run_parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model ID")
    run_parser.add_argument("--output", "-o", help="Save the report to a markdown file")
    run_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite the output file if it exists",
    )
    run_parser.add_argument("--parent", help="Continue from a previous interaction ID")

    # Think command
    think_parser = subparsers.add_parser(
        "think",
        help="Start a new thinking task",
        description="Start a new thinking task",
    )
    think_parser.add_argument("query", nargs="?", help="The thinking query")
    think_parser.add_argument(
        "--model", default=DEFAULT_THINK_MODEL, help="Gemini thinking model ID"
    )
    think_parser.add_argument(
        "--output", "-o", help="Save the response to a markdown file"
    )
    think_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite the output file if it exists",
    )
    think_parser.add_argument(
        "--api-version", default="v1alpha", help="API version (default: v1alpha)"
    )
    think_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for the thinking task (default: 1800)",
    )

    # List command
    subparsers.add_parser("list", help="List recent research tasks")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show details of a research task")
    show_parser.add_argument("id", type=int, help="The task ID")
    show_parser.add_argument(
        "--output", "-o", help="Save the report to a markdown file"
    )
    show_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite the output file if it exists",
    )

    args = parser.parse_args()

    try:
        if args.command == "run":
            if not args.query:
                run_parser.print_help()
                return
            asyncio.run(run_research_cmd(args))
        elif args.command == "think":
            if not args.query:
                think_parser.print_help()
                return
            asyncio.run(run_think_cmd(args))
        elif args.command == "list":
            list_tasks()
        elif args.command == "show":
            show_task(args.id, args.output, args.force)
        else:
            # Default behavior for backwards compatibility or direct script calls
            if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
                if script_name == "think":
                    asyncio.run(run_think(sys.argv[1], DEFAULT_THINK_MODEL))
                else:
                    asyncio.run(run_research(sys.argv[1], DEFAULT_MODEL))
            else:
                parser.print_help()
    except ResearchError:
        # Error messages are already printed by the functions
        sys.exit(1)
    except KeyboardInterrupt:
        get_console().print("\n[yellow]Research cancelled by user.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
