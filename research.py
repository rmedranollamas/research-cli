import os
import sys
import asyncio
import argparse
import sqlite3
from contextlib import contextmanager
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live

# Load environment variables from .env if present
load_dotenv()

# Configuration Constants
DB_PATH = os.getenv(
    "RESEARCH_DB_PATH", os.path.expanduser("~/.research-cli/history.db")
)
DEFAULT_MODEL = os.getenv("RESEARCH_MODEL", "deep-research-pro-preview-12-2025")
DEFAULT_THINK_MODEL = os.getenv("THINK_MODEL", "gemini-2.0-flash-thinking-exp")
QUERY_TRUNCATION_LENGTH = 50

RECENT_TASKS_LIMIT = 20
# Global Rich console
console = Console()


def get_val(obj, key: str, default=None):
    """Safely gets a value from an object or dictionary."""
    if obj is None:
        return default
    val = getattr(obj, key, None)
    if val is None and isinstance(obj, dict):
        return obj.get(key, default)
    return val if val is not None else default


@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
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
        conn.commit()


def save_task(query: str, model: str, interaction_id: Optional[str] = None, parent_id: Optional[str] = None):
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO research_tasks (query, model, interaction_id, status, parent_id) VALUES (?, ?, ?, ?, ?)",
            (query, model, interaction_id, "PENDING", parent_id),
        )
        task_id = cursor.lastrowid
        conn.commit()
        return task_id


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


async def run_research(query: str, model_id: str, parent_id: Optional[str] = None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    task_id = save_task(query, model_id, parent_id=parent_id)

    try:
        http_options = {"api_version": "v1alpha"}
        base_url = os.getenv("GEMINI_API_BASE_URL")
        if base_url:
            http_options["base_url"] = base_url

        client = genai.Client(api_key=api_key, http_options=http_options)
    except Exception:
        console.print("[red]Error initializing Gemini client:[/red]")
        console.print_exception()
        update_task(task_id, "ERROR", "Client initialization failed")
        sys.exit(1)

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
                        update_task(
                            task_id, "IN_PROGRESS", interaction_id=interaction_id
                        )
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
        update_task(task_id, "ERROR", "Research execution failed")
        return None

    if report_content:
        update_task(task_id, "COMPLETED", report_content)
        console.print("\n" + "=" * 40 + "\n")
        console.print(Markdown(report_content))
        console.print("\n" + "=" * 40 + "\n")

        return report_content
    else:
        update_task(task_id, "FAILED")
        console.print("[yellow]No report content received.[/yellow]")
        return None


async def run_research_cmd(args):
    parent_id = args.parent
    report = await run_research(args.query, args.model, parent_id=parent_id)
    if report and args.output:
        with open(args.output, "w") as f:
            f.write(report)
        console.print(f"[green]Report saved to {args.output}[/green]")


async def run_think(
    query: str, model_id: str, api_version: str = "v1alpha", timeout: int = 1800
):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    task_id = save_task(query, model_id)

    try:
        http_options = {"api_version": api_version, "timeout": timeout}
        base_url = os.getenv("GEMINI_API_BASE_URL")
        if base_url:
            http_options["base_url"] = base_url

        client = genai.Client(api_key=api_key, http_options=http_options)
    except Exception:
        console.print("[red]Error initializing Gemini client:[/red]")
        console.print_exception()
        update_task(task_id, "ERROR", "Client initialization failed")
        sys.exit(1)

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
        update_task(task_id, "ERROR", "Execution failed")
        return None

    if report_content:
        update_task(task_id, "COMPLETED", report_content)
        console.print("\n" + "=" * 40 + "\n")
        console.print(Markdown(report_content))
        console.print("\n" + "=" * 40 + "\n")

        return report_content
    else:
        update_task(task_id, "FAILED")
        console.print("[yellow]No content received.[/yellow]")
        return None


async def run_think_cmd(args):
    report = await run_think(
        args.query, args.model, api_version=args.api_version, timeout=args.timeout
    )
    if report and args.output:
        with open(args.output, "w") as f:
            f.write(report)
        console.print(f"[green]Saved to {args.output}[/green]")


def show_task(task_id: int, output_file: Optional[str] = None):
    init_db()
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
            with open(output_file, "w") as f:
                f.write(report)
            console.print(f"[green]Report saved to {output_file}[/green]")
    else:
        console.print("[yellow]No report content available for this task.[/yellow]")


def list_tasks():
    init_db()
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
        display_query = (
            (query[: QUERY_TRUNCATION_LENGTH - 3] + "...")
            if len(query) > QUERY_TRUNCATION_LENGTH
            else query
        )
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
    run_parser.add_argument("--parent", help="Continue from a previous interaction ID")

    # Think command
    think_parser = subparsers.add_parser(
        "think", help="Start a new thinking task", description="Start a new thinking task"
    )
    think_parser.add_argument("query", nargs="?", help="The thinking query")
    think_parser.add_argument(
        "--model", default=DEFAULT_THINK_MODEL, help="Gemini thinking model ID"
    )
    think_parser.add_argument(
        "--output", "-o", help="Save the response to a markdown file"
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
            show_task(args.id, args.output)
        else:
            # Default behavior for backwards compatibility or direct script calls
            if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
                if script_name == "think":
                    asyncio.run(run_think(sys.argv[1], DEFAULT_THINK_MODEL))
                else:
                    asyncio.run(run_research(sys.argv[1], DEFAULT_MODEL))
            else:
                parser.print_help()
    except KeyboardInterrupt:
        console.print("\n[yellow]Research cancelled by user.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
