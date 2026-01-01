import os
import sys
import asyncio
from google import genai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


async def run_research(query: str, model_id: str = "deep-research-pro-preview-12-2025"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})

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

        report_content = ""
        current_thought = ""

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Researching...", total=None)

            for event in stream:
                # The event structure in v1alpha/Interactions can be:
                # event.thought
                # event.content.parts
                # event.interaction (metadata)

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
                            report_content += text
                            # If we are streaming the final report, we might want to update the UI
                            # But for deep research, thoughts are the main stream, report comes at the end.

            progress.update(task, description="Research complete!", completed=True)

        if report_content:
            console.print("\n" + "=" * 40 + "\n")
            console.print(Markdown(report_content))
            console.print("\n" + "=" * 40 + "\n")
        else:
            console.print("[yellow]No report content received.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during research:[/red] {str(e)}")
        # If it's a 404 or model not found, explain
        if "404" in str(e):
            console.print(
                "[yellow]Note: The Interactions API and deep-research model might require specific whitelist access or v1alpha version.[/yellow]"
            )


def main():
    if len(sys.argv) < 2:
        console.print('[yellow]Usage: research "your research query"[/yellow]')
        sys.exit(1)

    query = sys.argv[1]
    asyncio.run(run_research(query))


if __name__ == "__main__":
    main()
