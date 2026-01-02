import os
import sys
import asyncio
import argparse
from typing import List
from google import genai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


async def run_research(query: str, model_id: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

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

    # Config for deep research
    config = {
        "background": True,
        "stream": True,
        "agent_config": {"thinking_summaries": "auto"},
    }

    try:
        # The Interactions API
        stream = client.interactions.create(
            model=model_id, contents=query, config=config
        )

        report_parts: List[str] = []
        current_thought = ""

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Researching...", total=None)

            for event in stream:
                # Update thought if available
                thought = getattr(event, "thought", None)
                if thought:
                    current_thought = thought
                    progress.update(
                        task,
                        description=f"[italic grey]{current_thought}[/italic grey]",
                    )

                # Update content if available
                content = getattr(event, "content", None)
                if content:
                    parts = getattr(content, "parts", [])
                    for part in parts:
                        text = getattr(part, "text", None)
                        if text:
                            report_parts.append(text)

            progress.update(task, description="Research complete!", completed=True)

        report_content = "".join(report_parts)
        if report_content:
            console.print("\n" + "=" * 40 + "\n")
            console.print(Markdown(report_content))
            console.print("\n" + "=" * 40 + "\n")
        else:
            console.print("[yellow]No report content received.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during research interaction:[/red] {str(e)}")
        if "404" in str(e):
            console.print(
                "[yellow]Note: Ensure the model ID is correct and you have access to the Interactions API.[/yellow]"
            )


def main():
    parser = argparse.ArgumentParser(description="Gemini Deep Research CLI")
    parser.add_argument("query", help="The research query")
    parser.add_argument(
        "--model", default="deep-research-pro-preview-12-2025", help="Gemini model ID"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_research(args.query, args.model))
    except KeyboardInterrupt:
        console.print("\n[yellow]Research cancelled by user.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
