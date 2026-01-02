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
                # Get interaction ID if available
                inter = getattr(event, "interaction", None)
                if inter and not interaction_id:
                    interaction_id = getattr(inter, "id", None)
                    if interaction_id:
                        progress.update(
                            task, description=f"Researching (ID: {interaction_id})..."
                        )

                # Handle thoughts
                thought = getattr(event, "thought", None)
                if thought:
                    progress.update(
                        task, description=f"[italic grey]{thought}[/italic grey]"
                    )
                    console.print(f"[italic grey]> {thought}[/italic grey]")

                # Handle content
                content = getattr(event, "content", None)
                if content:
                    parts = getattr(content, "parts", [])
                    for part in parts:
                        text = getattr(part, "text", None)
                        if text:
                            report_parts.append(text)

            progress.update(task, description="Stream finished.", completed=True)

        report_content = "".join(report_parts)

        # Fallback: if stream finished but no content, poll the interaction
        if not report_content and interaction_id:
            console.print("[yellow]Checking final interaction state...[/yellow]")
            while True:
                final_inter = client.interactions.get(id=interaction_id)
                # Check state: 'COMPLETED', 'FAILED', etc.
                state = getattr(final_inter, "state", "UNKNOWN")
                if state == "COMPLETED":
                    # Extract response
                    response = getattr(final_inter, "response", None)
                    if response:
                        # Extract text from response (similar to GenerateContentResponse)
                        if hasattr(response, "candidates"):
                            for cand in response.candidates:
                                if cand.content and cand.content.parts:
                                    for part in cand.content.parts:
                                        if part.text:
                                            report_parts.append(part.text)
                        elif hasattr(response, "text"):
                            report_parts.append(response.text)
                    break
                elif state in ["FAILED", "CANCELLED"]:
                    console.print(f"[red]Research interaction {state.lower()}.[/red]")
                    break
                else:
                    # Still running? Wait a bit
                    await asyncio.sleep(5)

            report_content = "".join(report_parts)

        if report_content:
            console.print("\n" + "=" * 40 + "\n")
            console.print(Markdown(report_content))
            console.print("\n" + "=" * 40 + "\n")
        else:
            console.print("[yellow]No report content received.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during research interaction:[/red] {str(e)}")


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
