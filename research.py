import os
import sys
import asyncio
import argparse
import sqlite3
from typing import List, Optional
from google import genai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
DB_PATH = os.path.expanduser("~/.research-cli/history.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id TEXT UNIQUE,
            query TEXT,
            model TEXT,
            status TEXT,
            report TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def save_task(query: str, model: str, interaction_id: Optional[str] = None):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO research_tasks (query, model, interaction_id, status) VALUES (?, ?, ?, ?)",
        (query, model, interaction_id, "PENDING"),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def update_task(
    task_id: int,
    status: str,
    report: Optional[str] = None,
    interaction_id: Optional[str] = None,
):
    conn = init_db()
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
    conn.close()


async def run_research(query: str, model_id: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    task_id = save_task(query, model_id)

    try:
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
    except Exception as e:
        console.print(f"[red]Error initializing Gemini client:[/red] {str(e)}")
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
                inter = getattr(event, "interaction", None)
                if inter and not interaction_id:
                    interaction_id = getattr(inter, "id", None)
                    if interaction_id:
                        update_task(
                            task_id, "IN_PROGRESS", interaction_id=interaction_id
                        )
                        progress.update(
                            task, description=f"Researching (ID: {interaction_id})..."
                        )

                thought = getattr(event, "thought", None)
                if thought:
                    progress.update(
                        task, description=f"[italic grey]{thought}[/italic grey]"
                    )
                    console.print(f"[italic grey]> {thought}[/italic grey]")

                content = getattr(event, "content", None)
                if content:
                    parts = getattr(content, "parts", [])
                    for part in parts:
                        text = getattr(part, "text", None)
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
                status = getattr(final_inter, "status", "UNKNOWN").upper()
                if status != last_status:
                    console.print(f"[dim]Current status: {status}[/dim]")
                    last_status = status

                if status == "COMPLETED":
                    outputs = getattr(final_inter, "outputs", [])
                    for output in outputs:
                        if hasattr(output, "text") and output.text:
                            report_parts.append(output.text)
                    if not report_parts:
                        response = getattr(final_inter, "response", None)
                        if response and hasattr(response, "text"):
                            report_parts.append(response.text)
                    break
                elif status in ["FAILED", "CANCELLED"]:
                    break
                await asyncio.sleep(10)

            report_content = "".join(report_parts)

        if report_content:
            update_task(task_id, "COMPLETED", report_content)
            console.print("\n" + "=" * 40 + "\n")
            console.print(Markdown(report_content))
            console.print("\n" + "=" * 40 + "\n")
        else:
            update_task(task_id, "FAILED")
            console.print("[yellow]No report content received.[/yellow]")

    except Exception as e:
        update_task(task_id, "ERROR", str(e))
        console.print(f"[red]Error during research interaction:[/red] {str(e)}")


def list_tasks():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, query, status, created_at FROM research_tasks ORDER BY created_at DESC LIMIT 20"
    )
    tasks = cursor.fetchall()
    conn.close()

    table = Table(title="Recent Research Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Query", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created At", style="dim")

    for task in tasks:
        table.add_row(
            str(task[0]),
            task[1][:50] + ("..." if len(task[1]) > 50 else ""),
            task[2],
            task[3],
        )

    console.print(table)


def show_task(task_id: int):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT query, report, status FROM research_tasks WHERE id = ?", (task_id,)
    )
    task = cursor.fetchone()
    conn.close()

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
    else:
        console.print("[yellow]No report content available for this task.[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Gemini Deep Research CLI")
    parser.add_argument("--version", action="version", version="research-cli 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Start a new research task")
    run_parser.add_argument("query", help="The research query")
    run_parser.add_argument(
        "--model", default="deep-research-pro-preview-12-2025", help="Gemini model ID"
    )

    # List command
    subparsers.add_parser("list", help="List recent research tasks")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show details of a research task")
    show_parser.add_argument("id", type=int, help="The task ID")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_research(args.query, args.model))
    elif args.command == "list":
        list_tasks()
    elif args.command == "show":
        show_task(args.id)
    else:
        # Default behavior for backwards compatibility if no subcommand is provided
        # Though with subparsers, it usually requires one unless we handle it
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # If the first arg is not a command but looks like a query
            asyncio.run(run_research(sys.argv[1], "deep-research-pro-preview-12-2025"))
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
