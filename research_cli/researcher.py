import asyncio
import os
from typing import List, Optional, Set
from google import genai
from .db import async_save_task, async_update_task
from .utils import get_console, get_val, print_report
from .config import POLL_INTERVAL_DEFAULT, ResearchError


class ResearchAgent:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.console = get_console()

    def get_client(
        self,
        api_version: str = "v1alpha",
        timeout: Optional[int] = None,
    ) -> genai.Client:
        http_options = {"api_version": api_version}
        if timeout is not None:
            http_options["timeout"] = timeout
        if self.base_url:
            http_options["base_url"] = self.base_url

        try:
            return genai.Client(api_key=self.api_key, http_options=http_options)
        except Exception:
            # Note: This doesn't update the task because it doesn't know the task_id
            # The caller should handle task update
            raise ResearchError("Client initialization failed")

    async def _handle_error(
        self,
        task_id: int,
        prefix: str,
        db_msg: str,
        inter_id: Optional[str] = None,
        bg_tasks: Optional[Set] = None,
    ):
        self.console.print(f"[red]{prefix}:[/red]")
        self.console.print_exception()
        if bg_tasks:
            await asyncio.gather(*bg_tasks, return_exceptions=True)
        await async_update_task(task_id, "ERROR", db_msg, interaction_id=inter_id)

    async def _poll_interaction(
        self, client: genai.Client, interaction_id: str, report_parts: List[str]
    ):
        self.console.print(
            f"[yellow]Stream ended without report. Polling interaction {interaction_id}...[/yellow]"
        )
        last_status = None
        try:
            max_interval = float(
                os.getenv("RESEARCH_POLL_INTERVAL", str(POLL_INTERVAL_DEFAULT))
            )
        except ValueError:
            max_interval = POLL_INTERVAL_DEFAULT

        max_interval = max(1.0, max_interval)
        current_interval = 1.0
        while True:
            try:
                final_inter = await client.aio.interactions.get(id=interaction_id)
            except Exception as e:
                # Handle transient server errors (500, 503) during polling
                if "500" in str(e) or "503" in str(e):
                    self.console.print(
                        f"[dim]Transient API error ({e}), retrying in {current_interval}s...[/dim]"
                    )
                    await asyncio.sleep(current_interval)
                    current_interval = min(current_interval * 1.5, max_interval)
                    continue
                raise e

            status = get_val(final_inter, "status", "UNKNOWN").upper()
            if status != last_status:
                self.console.print(f"[dim]Current status: {status}[/dim]")
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

            await asyncio.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_interval)
        return "".join(report_parts)

    async def run_research(
        self, query: str, model_id: str, parent_id: Optional[str] = None
    ):
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn

        task_id = await async_save_task(query, model_id, parent_id=parent_id)

        try:
            client = self.get_client()
        except Exception:
            await self._handle_error(
                task_id,
                "Error initializing Gemini client",
                "Client initialization failed",
            )
            raise ResearchError("Client initialization failed")

        self.console.print(
            Panel(
                f"[bold blue]Query:[/bold blue] {query}\n[bold blue]Model:[/bold blue] {model_id}",
                title="Deep Research Starting",
            )
        )

        report_parts: List[str] = []
        interaction_id = None
        background_tasks = set()

        try:
            stream = await client.aio.interactions.create(
                agent=model_id,
                input=query,
                background=True,
                stream=True,
                agent_config={"type": "deep-research", "thinking_summaries": "auto"},
                previous_interaction_id=parent_id,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Initializing...", total=None)
                async for event in stream:
                    inter = get_val(event, "interaction")
                    if inter and not interaction_id:
                        interaction_id = get_val(inter, "id")
                        if interaction_id:
                            job = asyncio.create_task(
                                async_update_task(
                                    task_id,
                                    "IN_PROGRESS",
                                    interaction_id=interaction_id,
                                )
                            )
                            background_tasks.add(job)
                            job.add_done_callback(background_tasks.discard)
                            progress.update(
                                task,
                                description=f"Researching (ID: {interaction_id})...",
                            )

                    thought = get_val(event, "thought")
                    if thought:
                        progress.update(
                            task, description=f"[italic grey]{thought}[/italic grey]"
                        )
                        self.console.print(f"[italic grey]> {thought}[/italic grey]")

                    content = get_val(event, "content")
                    if content:
                        parts = get_val(content, "parts", [])
                        for part in parts:
                            text = get_val(part, "text")
                            if text:
                                report_parts.append(text)

                progress.update(task, description="Stream finished.", completed=True)

            if background_tasks:
                await asyncio.gather(*background_tasks, return_exceptions=True)

            report_content = "".join(report_parts)
            if not report_content and interaction_id:
                report_content = await self._poll_interaction(
                    client, interaction_id, report_parts
                )

        except Exception:
            await self._handle_error(
                task_id,
                "Error during research",
                "Research execution failed",
                interaction_id,
                background_tasks,
            )
            return None

        if report_content:
            await async_update_task(task_id, "COMPLETED", report_content)
            print_report(report_content)
            return report_content

        await async_update_task(task_id, "FAILED")
        self.console.print("[yellow]No report content received.[/yellow]")
        return None
