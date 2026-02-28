import argparse
import sys
import os
import asyncio
from .config import DEFAULT_MODEL, ResearchError, RESEARCH_API_KEY_VAR
from .db import async_get_task, async_get_recent_tasks
from .utils import (
    get_console,
    truncate_query,
    async_save_report_to_file,
    print_report,
)
from .researcher import ResearchAgent
from importlib import metadata

# Try to get version from package metadata or pyproject.toml
try:
    VERSION = metadata.version("research-cli")
except metadata.PackageNotFoundError:
    try:
        import tomllib
        from pathlib import Path

        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                VERSION = tomllib.load(f)["project"]["version"]
        else:
            VERSION = "unknown"
    except (ImportError, FileNotFoundError, KeyError):
        VERSION = "unknown"


def create_parser():
    script_name = os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(description="Gemini Deep Research CLI")
    parser.add_argument(
        "--version", action="version", version=f"research-cli {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common arguments
    def add_common_args(p):
        p.add_argument("query", nargs="?", help="The query to process")
        p.add_argument("--output", "-o", help="Save the result to a file")
        p.add_argument(
            "--force", "-f", action="store_true", help="Overwrite existing output file"
        )

    # Run command
    run_parser = subparsers.add_parser("run", help="Start deep research")
    add_common_args(run_parser)
    run_parser.add_argument("--model", default=DEFAULT_MODEL, help="Model ID")
    run_parser.add_argument("--parent", help="Previous interaction ID")
    run_parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        help="Include URL in context (can be repeated)",
    )
    run_parser.add_argument(
        "--file",
        action="append",
        dest="files",
        help="Include local file in context (can be repeated)",
    )
    run_parser.add_argument(
        "--thinking",
        choices=["minimal", "low", "medium", "high"],
        help="Thinking level (for supported models)",
    )
    run_parser.add_argument(
        "--no-search",
        action="store_false",
        dest="use_search",
        help="Disable Google Search grounding",
    )
    run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show reasoning thoughts"
    )
    run_parser.set_defaults(use_search=True)

    # Search command (Fast grounding)
    search_parser = subparsers.add_parser("search", help="Fast grounding search")
    add_common_args(search_parser)
    search_parser.add_argument("--model", default="gemini-2.0-flash", help="Model ID")
    search_parser.add_argument("--parent", help="Previous interaction ID")
    search_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show reasoning thoughts"
    )

    # Status command
    status_parser = subparsers.add_parser(
        "status", help="Check status of a research task by Interaction ID"
    )
    status_parser.add_argument("interaction_id", help="Interaction ID to check")
    status_parser.add_argument(
        "--output", "-o", help="Save report to file if completed"
    )
    status_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing file"
    )

    # Image generation command
    image_parser = subparsers.add_parser(
        "generate-image", help="Generate an image from a prompt"
    )
    image_parser.add_argument("prompt", help="The image prompt")
    image_parser.add_argument(
        "--output", "-o", default="generated_image.png", help="Output file path"
    )
    image_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing file"
    )
    image_parser.add_argument(
        "--model", default="gemini-3-pro-image-preview", help="Model ID"
    )

    # List command
    subparsers.add_parser("list", help="List recent research tasks")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show details of a research task")
    show_parser.add_argument("id", type=int, help="Task ID")
    show_parser.add_argument("--output", "-o", help="Save report to file")
    show_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing file"
    )

    return parser, script_name


async def handle_run(args, agent: ResearchAgent, parser):
    if not args.query:
        subparsers_action = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        subparsers_action.choices["run"].print_help()
        return

    report = await agent.run_research(
        args.query,
        args.model,
        parent_id=args.parent,
        urls=args.urls,
        files=args.files,
        use_search=args.use_search,
        thinking_level=args.thinking,
        verbose=args.verbose,
    )
    if report and args.output:
        await async_save_report_to_file(report, args.output, args.force)


async def handle_search(args, agent: ResearchAgent, parser):
    if not args.query:
        subparsers_action = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        subparsers_action.choices["search"].print_help()
        return

    report = await agent.run_search(
        args.query,
        args.model,
        parent_id=args.parent,
        verbose=args.verbose,
    )
    if report and args.output:
        await async_save_report_to_file(report, args.output, args.force)


async def handle_status(args, agent: ResearchAgent):
    report = await agent.get_status(args.interaction_id)
    if report and args.output:
        await async_save_report_to_file(report, args.output, args.force)


async def handle_generate_image(args, agent: ResearchAgent):
    await agent.generate_image(args.prompt, args.output, args.model, args.force)


async def handle_list():
    from rich.table import Table

    tasks = await async_get_recent_tasks(20)
    if not tasks:
        get_console().print("[yellow]No research tasks found in history.[/yellow]")
        return

    table = Table(title="Recent Research Tasks")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Query", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created At", style="magenta")
    table.add_column("Interaction ID", style="dim")

    for tid, q, status, dt, iid in tasks:
        table.add_row(str(tid), truncate_query(q), status, dt, iid or "-")
    get_console().print(table)


async def handle_show(args):
    from rich.panel import Panel

    task = await async_get_task(args.id)
    if not task:
        get_console().print(f"[red]Task {args.id} not found.[/red]")
        return

    q, report, status = task
    get_console().print(
        Panel(
            f"[bold blue]Query:[/bold blue] {q}\n[bold blue]Status:[/bold blue] {status}",
            title=f"Research Task {args.id}",
        )
    )
    if report:
        print_report(report)
        if args.output:
            await async_save_report_to_file(report, args.output, args.force)
    else:
        get_console().print(
            "[yellow]No report content available for this task.[/yellow]"
        )


# Function to get API key (moved out of main_async to be importable)
def get_api_key():
    api_key = os.getenv(RESEARCH_API_KEY_VAR)  # Use the new RESEARCH_API_KEY_VAR
    if not api_key:
        get_console().print(
            f"[red]Error: {RESEARCH_API_KEY_VAR} environment variable not set.[/red]"
        )
        raise ResearchError(f"{RESEARCH_API_KEY_VAR} environment variable not set.")
    return api_key


async def main_async():
    parser, script_name = create_parser()
    args = parser.parse_args()

    if args.command in ["run", "search", "status", "generate-image"] or (
        not args.command and len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    ):
        try:
            # get_api_key is now a separate function
            api_key = get_api_key()

            agent = ResearchAgent(api_key, os.getenv("GEMINI_API_BASE_URL"))

            if args.command == "run":
                await handle_run(args, agent, parser)
            elif args.command == "search":
                await handle_search(args, agent, parser)
            elif args.command == "status":
                await handle_status(args, agent)
            elif args.command == "generate-image":
                await handle_generate_image(args, agent)
            else:
                query = sys.argv[1]
                await agent.run_research(query, DEFAULT_MODEL)
        except ResearchError:
            sys.exit(1)
        except KeyboardInterrupt:
            get_console().print("\n[yellow]Cancelled by user.[/yellow]")
            sys.exit(0)
    elif args.command == "list":
        await handle_list()
    elif args.command == "show":
        await handle_show(args)
    else:
        parser.print_help()


def main():
    asyncio.run(main_async())
