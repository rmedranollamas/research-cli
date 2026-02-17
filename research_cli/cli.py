import argparse
import sys
import os
import asyncio
from .config import DEFAULT_MODEL, DEFAULT_THINK_MODEL, ResearchError
from .db import get_task, get_recent_tasks
from .utils import get_console, truncate_query, save_report_to_file, print_report
from .researcher import ResearchAgent


def create_parser():
    script_name = os.path.basename(sys.argv[0])

    # If called via 'think' entry point, default to 'think' subcommand
    if (
        script_name == "think"
        and len(sys.argv) > 1
        and sys.argv[1]
        not in ["run", "think", "list", "show", "-h", "--help", "--version"]
    ):
        sys.argv.insert(1, "think")

    parser = argparse.ArgumentParser(description="Gemini Deep Research CLI")
    parser.add_argument("--version", action="version", version="research-cli 0.1.0")

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

    # Think command
    think_parser = subparsers.add_parser(
        "think",
        help="Start a new thinking task",
        description="Start a new thinking task",
    )
    add_common_args(think_parser)
    think_parser.add_argument("--model", default=DEFAULT_THINK_MODEL, help="Model ID")
    think_parser.add_argument("--api-version", default="v1alpha", help="API version")
    think_parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout in seconds"
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
        # Match old behavior: print help for the subcommand
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for name, subparser in subparsers_action.choices.items():
                if name == "run":
                    subparser.print_help()
                    return
        return
    report = await agent.run_research(args.query, args.model, parent_id=args.parent)
    if report and args.output:
        save_report_to_file(report, args.output, args.force)


async def handle_think(args, agent: ResearchAgent, parser):
    if not args.query:
        # Match old behavior: print help for the subcommand
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for name, subparser in subparsers_action.choices.items():
                if name == "think":
                    subparser.print_help()
                    return
        return
    report = await agent.run_think(
        args.query, args.model, api_version=args.api_version, timeout=args.timeout
    )
    if report and args.output:
        save_report_to_file(report, args.output, args.force, success_prefix="Saved to")


def handle_list():
    from rich.table import Table

    tasks = get_recent_tasks(20)
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


def handle_show(args):
    from rich.panel import Panel

    task = get_task(args.id)
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
            save_report_to_file(report, args.output, args.force)
    else:
        get_console().print(
            "[yellow]No report content available for this task.[/yellow]"
        )


async def main_async():
    parser, script_name = create_parser()
    args = parser.parse_args()

    if args.command in ["run", "think"] or (
        not args.command and len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    ):
        try:
            from . import get_api_key

            api_key = get_api_key()

            agent = ResearchAgent(api_key, os.getenv("GEMINI_API_BASE_URL"))

            if args.command == "run":
                await handle_run(args, agent, parser)
            elif args.command == "think":
                await handle_think(args, agent, parser)
            else:
                # Default behavior
                query = sys.argv[1]
                if script_name == "think":
                    await agent.run_think(query, DEFAULT_THINK_MODEL)
                else:
                    await agent.run_research(query, DEFAULT_MODEL)
        except ResearchError:
            sys.exit(1)
        except KeyboardInterrupt:
            get_console().print("\n[yellow]Cancelled by user.[/yellow]")
            sys.exit(0)
    elif args.command == "list":
        handle_list()
    elif args.command == "show":
        handle_show(args)
    else:
        parser.print_help()


def main():
    asyncio.run(main_async())
