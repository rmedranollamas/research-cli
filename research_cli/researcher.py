import asyncio
import os
import base64
from typing import List, Optional, Set, Any, Dict, cast
from google import genai
from .db import async_save_task, async_update_task
from .utils import get_console, get_val, print_report
from .config import POLL_INTERVAL_DEFAULT, ResearchError, RESEARCH_MCP_SERVERS


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
        http_options: Any = {"api_version": api_version}
        if timeout is not None:
            http_options["timeout"] = timeout
        if self.base_url:
            http_options["base_url"] = self.base_url

        try:
            return genai.Client(api_key=self.api_key, http_options=http_options)  # type: ignore
        except Exception:
            raise ResearchError("Client initialization failed")

    async def _handle_error(
        self,
        task_id: int,
        prefix: str,
        db_msg: str,
        inter_id: Optional[str] = None,
        bg_tasks: Optional[Set[asyncio.Task]] = None,
    ):
        self.console.print(f"[red]{prefix}:[/red]")
        self.console.print_exception()
        if bg_tasks:
            await asyncio.gather(*bg_tasks, return_exceptions=True)
        await async_update_task(task_id, "ERROR", db_msg, interaction_id=inter_id)

    async def _poll_interaction(
        self, client: genai.Client, interaction_id: str, report_parts: List[str]
    ):
        from rich.text import Text

        self.console.print(
            Text.assemble(
                ("Stream ended without report. Polling interaction ", "yellow"),
                (interaction_id, "bold yellow"),
                ("...", "yellow"),
            )
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
                err_str = str(e)
                if "500" in err_str or "503" in err_str:
                    self.console.print(
                        Text(
                            f"Transient API error, retrying in {current_interval:.1f}s...",
                            style="dim",
                        )
                    )
                    await asyncio.sleep(current_interval)
                    current_interval = min(current_interval * 1.5, max_interval)
                    continue
                raise e

            status = get_val(final_inter, "status", "UNKNOWN").upper()
            if status != last_status:
                self.console.print(Text(f"Current status: {status}", style="dim"))
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

    def _get_tools(
        self,
        use_search: bool = False,
        urls: Optional[List[str]] = None,
    ) -> List[dict[str, Any]]:
        tools = []
        if use_search:
            tools.append({"type": "google_search"})
        if urls:
            tools.append({"type": "url_context"})

        for i, mcp_url in enumerate(RESEARCH_MCP_SERVERS):
            tools.append(
                {"type": "mcp_server", "name": f"mcp_server_{i}", "url": mcp_url}
            )
        return tools

    async def _upload_files(
        self, client: genai.Client, file_paths: List[str]
    ) -> List[str]:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.text import Text

        uploaded_uris = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for path in file_paths:
                if not os.path.exists(path):
                    self.console.print(
                        Text.assemble(
                            ("Error: File ", "red"),
                            (path, "bold red"),
                            (" not found.", "red"),
                        )
                    )
                    continue

                filename = os.path.basename(path)
                task = progress.add_task(f"Uploading {filename}...", total=None)
                try:
                    # Note: Files API is not yet available in aio, using sync call in thread
                    file_obj = await asyncio.to_thread(client.files.upload, file=path)
                    progress.update(task, description=f"Processing {filename}...")

                    file_uri = None
                    while True:
                        # Ty helper to avoid None name issue
                        name = cast(str, file_obj.name)
                        file_status = await asyncio.to_thread(
                            client.files.get, name=name
                        )
                        state = get_val(file_status, "state")
                        state_name = get_val(state, "name") if state else "UNKNOWN"

                        if state_name == "ACTIVE":
                            file_uri = get_val(file_status, "uri")
                            break
                        elif state_name in ["FAILED", "DELETED"]:
                            self.console.print(
                                Text.assemble(
                                    ("Error: File ", "red"),
                                    (path, "bold red"),
                                    (" failed to process.", "red"),
                                )
                            )
                            break
                        await asyncio.sleep(2)

                    if file_uri:
                        uploaded_uris.append(file_uri)
                        progress.update(
                            task,
                            description=f"Uploaded {filename}",
                            completed=True,
                        )
                    else:
                        progress.remove_task(task)
                except Exception as e:
                    self.console.print(
                        Text.assemble(
                            ("Error uploading ", "red"),
                            (path, "bold red"),
                            (f": {e}", "red"),
                        )
                    )
                    progress.remove_task(task)

        return uploaded_uris

    async def _run_interaction(
        self,
        task_id: int,
        query: str,
        interaction_params: Dict[str, Any],
        verbose: bool = False,
        error_prefix: str = "Error during research",
        error_msg: str = "Execution failed",
    ) -> Optional[str]:
        from rich.text import Text
        from rich.progress import Progress, SpinnerColumn, TextColumn

        try:
            client = self.get_client()
        except Exception:
            await self._handle_error(
                task_id,
                "Error initializing Gemini client",
                "Client initialization failed",
            )
            raise ResearchError("Client initialization failed")

        report_parts: List[str] = []
        interaction_id = None
        background_tasks: Set[asyncio.Task] = set()

        try:
            # We use cast(Any) because Interactions API has complex overloads that Ty struggles with
            stream = await cast(Any, client.aio.interactions.create)(
                **interaction_params
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                progress_task = progress.add_task("Initializing...", total=None)
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
                                progress_task,
                                description=f"Processing (ID: {interaction_id})...",
                            )

                    thought = get_val(event, "thought")
                    if thought:
                        summary = get_val(thought, "summary") or get_val(
                            thought,
                            "text",
                        )
                        if verbose and summary:
                            self.console.print("> ", end="")
                            self.console.print(Text(summary, style="italic grey"))

                        desc_text = summary if summary else "Thinking..."
                        progress.update(
                            progress_task,
                            description=f"[italic grey]{desc_text}[/italic grey]",
                        )

                    content = get_val(event, "content")
                    if content:
                        parts = get_val(content, "parts", [])
                        for part in parts:
                            text = get_val(part, "text")
                            if text:
                                report_parts.append(text)

                progress.update(
                    progress_task, description="Stream finished.", completed=True
                )

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
                error_prefix,
                error_msg,
                interaction_id,
                background_tasks,
            )
            return None

        if report_content:
            await async_update_task(task_id, "COMPLETED", report_content)
            print_report(report_content)
            return report_content

        await async_update_task(task_id, "FAILED")
        self.console.print(Text("No content received.", style="yellow"))
        return None

    async def run_research(
        self,
        query: str,
        model_id: str,
        parent_id: Optional[str] = None,
        urls: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        use_search: bool = True,
        thinking_level: Optional[str] = None,
        verbose: bool = False,
    ):
        from rich.panel import Panel
        from rich.text import Text

        task_id = await async_save_task(query, model_id, parent_id=parent_id)

        info_text = Text.assemble(
            ("Query: ", "bold blue"),
            (f"{query}\n", "white"),
            ("Model: ", "bold blue"),
            (f"{model_id}\n", "white"),
        )
        if parent_id:
            info_text.append("Parent ID: ", style="bold blue")
            info_text.append(f"{parent_id}\n", style="white")
        if urls:
            info_text.append("URLs: ", style="bold blue")
            info_text.append(f"{', '.join(urls)}\n", style="white")
        if files:
            info_text.append("Files: ", style="bold blue")
            info_text.append(f"{', '.join(files)}\n", style="white")

        self.console.print(
            Panel(
                info_text,
                title="Deep Research Starting",
            )
        )

        try:
            client = self.get_client()
        except Exception:
            await self._handle_error(
                task_id,
                "Error initializing Gemini client",
                "Client initialization failed",
            )
            raise ResearchError("Client initialization failed")

        # Handle file uploads
        file_uris = []
        if files:
            file_uris = await self._upload_files(client, files)

        agent_config: dict[str, Any] = {
            "type": "deep-research",
            "thinking_summaries": "auto",
        }

        # Workaround for Interactions API current limitations with direct URL/File context:
        # We append them to the query so the model can fetch them via tools if enabled.
        modified_query = query
        if urls:
            modified_query += (
                "\n\nPlease use the following URLs as context:\n" + "\n".join(urls)
            )
        if file_uris:
            modified_query += (
                "\n\nPlease use the following uploaded files as context:\n"
                + "\n".join(file_uris)
            )

        interaction_input: List[dict[str, Any]] = [
            {
                "role": "user",
                "content": [{"type": "text", "text": modified_query}],
            }
        ]

        params = {
            "agent": model_id,
            "input": interaction_input,
            "background": True,
            "stream": True,
            "agent_config": agent_config,
            "tools": self._get_tools(use_search=use_search, urls=urls) or None,
            "previous_interaction_id": parent_id,
        }

        return await self._run_interaction(
            task_id,
            query,
            params,
            verbose=verbose,
            error_prefix="Error during research",
            error_msg="Research execution failed",
        )

    async def run_search(
        self,
        query: str,
        model_id: str = "gemini-2.0-flash",
        parent_id: Optional[str] = None,
        verbose: bool = False,
    ):
        from rich.panel import Panel
        from rich.text import Text

        task_id = await async_save_task(query, model_id, parent_id=parent_id)

        info_text = Text.assemble(
            ("Query: ", "bold blue"),
            (f"{query}\n", "white"),
            ("Model: ", "bold blue"),
            (f"{model_id}\n", "white"),
        )
        if parent_id:
            info_text.append("Parent ID: ", style="bold blue")
            info_text.append(f"{parent_id}\n", style="white")

        self.console.print(
            Panel(
                info_text,
                title="Fast Search Starting",
            )
        )

        params = {
            "model": model_id,
            "input": query,
            "stream": True,
            "tools": self._get_tools(use_search=True),
            "previous_interaction_id": parent_id,
        }

        return await self._run_interaction(
            task_id, query, params, verbose=verbose, error_prefix="Error during search"
        )

    async def get_status(self, interaction_id: str) -> Optional[str]:
        client = self.get_client()
        report_parts: List[str] = []
        return await self._poll_interaction(client, interaction_id, report_parts)

    async def generate_image(
        self, prompt: str, output_path: str, model_id: str, force: bool
    ):
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.text import Text

        if os.path.exists(output_path) and not force:
            self.console.print(
                Text.assemble(
                    ("Error: Output file ", "red"),
                    (output_path, "bold red"),
                    (" already exists. Use --force to overwrite.", "red"),
                )
            )
            return

        client = self.get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            progress.add_task(f"Generating image with {model_id}...", total=None)

            try:
                # Interactions API for image generation
                interaction = await cast(Any, client.aio.interactions.create)(
                    model=model_id,
                    input=prompt,
                    response_modalities=cast(Any, ["IMAGE"]),
                )

                outputs = get_val(interaction, "outputs", [])
                for output in outputs:
                    if get_val(output, "type") == "image":
                        data = get_val(output, "data")
                        if data:
                            with open(output_path, "wb") as f:
                                f.write(base64.b64decode(data))
                            self.console.print(
                                Text.assemble(
                                    ("Image saved to ", "green"),
                                    (output_path, "bold green"),
                                )
                            )
                            return

                self.console.print(Text("No image was generated.", style="yellow"))
            except Exception as e:
                self.console.print(Text(f"Error generating image: {e}", style="red"))
                self.console.print_exception()
