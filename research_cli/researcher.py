import asyncio
import os
import base64
from typing import List, Optional, Set, Any, Dict, cast, Tuple
from google import genai
from .db import async_save_task, async_update_task
from .utils import (
    get_console,
    get_val,
    print_report,
    validate_path,
    async_save_binary_to_file,
)
from .config import POLL_INTERVAL_DEFAULT, ResearchError, RESEARCH_MCP_SERVERS

# Pre-calculated list of MCP server tools for performance
_MCP_TOOLS: "Tuple[Dict[str, Any], ...]" = tuple(
    {"type": "mcp_server", "name": f"mcp_server_{i}", "url": mcp_url}
    for i, mcp_url in enumerate(RESEARCH_MCP_SERVERS)
)


class ResearchAgent:
    """Agent for running deep research, search, and image generation using Gemini Interactions API."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        console: Optional[Any] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.console = console or get_console()

    def get_client(
        self,
        api_version: str = "v1alpha",
        timeout: Optional[int] = None,
    ) -> genai.Client:
        """Initializes and returns the Gemini client."""
        http_options: Dict[str, Any] = {"api_version": api_version}
        if timeout is not None:
            http_options["timeout"] = timeout
        if self.base_url:
            http_options["base_url"] = self.base_url

        try:
            return genai.Client(api_key=self.api_key, http_options=http_options)  # type: ignore
        except Exception as e:
            raise ResearchError(f"Client initialization failed: {e}")

    async def _handle_error(
        self,
        task_id: int,
        prefix: str,
        db_msg: str,
        inter_id: Optional[str] = None,
        bg_tasks: Optional[Set[asyncio.Task]] = None,
    ):
        """Unified error handling for research tasks."""
        self.console.print(f"[red]{prefix}:[/red]")
        self.console.print_exception()
        if bg_tasks:
            # Gather remaining background tasks if any
            await asyncio.gather(*bg_tasks, return_exceptions=True)
        await async_update_task(task_id, "ERROR", db_msg, interaction_id=inter_id)

    async def _poll_interaction(
        self, client: genai.Client, interaction_id: str, report_parts: List[str]
    ) -> str:
        """Polls an interaction until completion or failure."""
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
            max_poll_interval = float(
                os.getenv("RESEARCH_POLL_INTERVAL", str(POLL_INTERVAL_DEFAULT))
            )
        except ValueError:
            max_poll_interval = POLL_INTERVAL_DEFAULT

        max_poll_interval = max(1.0, max_poll_interval)
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
                    current_interval = min(current_interval * 1.5, max_poll_interval)
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
                error_msg = f"Interaction {status.lower()}"
                if status == "FAILED":
                    error_details = get_val(final_inter, "error")
                    if error_details:
                        error_msg += f": {error_details}"
                raise ResearchError(error_msg)

            await asyncio.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_poll_interval)

        return "".join(report_parts)

    def _get_tools(
        self,
        use_search: bool = False,
        urls: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Constructs and returns the list of tools for an interaction."""
        tools: List[Dict[str, Any]] = []
        if use_search:
            tools.append({"type": "google_search"})
        if urls:
            tools.append({"type": "url_context"})

        tools.extend(_MCP_TOOLS)
        return tools

    async def _upload_single_file(
        self,
        client: genai.Client,
        path: str,
        progress: Any,
    ) -> Optional[str]:
        """Uploads a single file and polls for its active status."""
        from rich.text import Text

        try:
            path = await asyncio.to_thread(validate_path, path)
        except ResearchError as e:
            self.console.print(Text(str(e), style="red"))
            return None

        if not await asyncio.to_thread(os.path.exists, path):
            self.console.print(
                Text.assemble(
                    ("Error: File ", "red"),
                    (path, "bold red"),
                    (" not found.", "red"),
                )
            )
            return None

        filename = os.path.basename(path)
        task = progress.add_task(f"Uploading {filename}...", total=None)
        try:
            # Note: Files API is not yet available in aio, using sync call in thread
            file_obj = await asyncio.to_thread(client.files.upload, file=path)
            progress.update(task, description=f"Processing {filename}...")

            file_uri = None
            while True:
                # Use cast to ensure name is string for the type checker
                name = cast(str, file_obj.name)
                file_status = await asyncio.to_thread(client.files.get, name=name)
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
                progress.update(
                    task,
                    description=f"Uploaded {filename}",
                    completed=True,
                )
                return file_uri
            else:
                progress.remove_task(task)
                return None
        except Exception as e:
            self.console.print(
                Text.assemble(
                    ("Error uploading ", "red"),
                    (path, "bold red"),
                    (f": {e}", "red"),
                )
            )
            progress.remove_task(task)
            return None

    async def _upload_files(
        self, client: genai.Client, file_paths: List[str]
    ) -> List[str]:
        """Uploads files to the Gemini Files API concurrently and returns their URIs."""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            tasks = [
                self._upload_single_file(client, path, progress) for path in file_paths
            ]
            results = await asyncio.gather(*tasks)

        return [uri for uri in results if uri is not None]

    async def _run_interaction(
        self,
        task_id: int,
        interaction_params: Dict[str, Any],
        verbose: bool = False,
        error_prefix: str = "Error during interaction",
        error_msg: str = "Execution failed",
    ) -> Optional[str]:
        """Internal helper to run and stream an interaction."""
        from rich.text import Text
        from rich.progress import Progress, SpinnerColumn, TextColumn

        try:
            client = self.get_client()
        except Exception as e:
            await self._handle_error(
                task_id,
                "Error initializing Gemini client",
                f"Client initialization failed: {e}",
            )
            return None

        report_parts: List[str] = []
        interaction_id: Optional[str] = None
        background_tasks: Set[asyncio.Task] = set()

        try:
            # Create the interaction stream
            # The interactions.create returns an async iterator
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
                    # Update interaction ID and DB status
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

                    # Handle thought blocks
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

                    # Handle content blocks
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

            # Ensure all background tasks are done
            if background_tasks:
                await asyncio.gather(*background_tasks, return_exceptions=True)

            # Polling fallback if stream didn't provide content
            report_content = "".join(report_parts)
            if not report_content and interaction_id:
                report_content = await self._poll_interaction(
                    client, interaction_id, report_parts
                )

        except Exception as e:
            await self._handle_error(
                task_id,
                error_prefix,
                f"{error_msg}: {e}",
                interaction_id,
                background_tasks,
            )
            return None

        # Success path
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
    ) -> Optional[str]:
        """Runs a deep research task."""
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
        except Exception as e:
            await self._handle_error(
                task_id,
                "Error initializing Gemini client",
                f"Client initialization failed: {e}",
            )
            return None

        # Handle file uploads
        file_uris: List[str] = []
        if files:
            file_uris = await self._upload_files(client, files)

        agent_config: Dict[str, Any] = {
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

        interaction_input: List[Dict[str, Any]] = [
            {
                "role": "user",
                "content": [{"type": "text", "text": modified_query}],
            }
        ]

        params: Dict[str, Any] = {
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
    ) -> Optional[str]:
        """Runs a fast grounded search interaction."""
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

        params: Dict[str, Any] = {
            "model": model_id,
            "input": query,
            "stream": True,
            "tools": self._get_tools(use_search=True),
            "previous_interaction_id": parent_id,
        }

        return await self._run_interaction(
            task_id,
            params,
            verbose=verbose,
            error_prefix="Error during search",
            error_msg="Search execution failed",
        )

    async def get_status(self, interaction_id: str) -> Optional[str]:
        """Polls for the status and result of an existing interaction."""
        try:
            client = await asyncio.to_thread(self.get_client)
        except Exception as e:
            raise ResearchError(f"Client initialization failed: {e}")
        report_parts: List[str] = []
        return await self._poll_interaction(client, interaction_id, report_parts)

    def _prepare_output_path(self, output_path: str, force: bool) -> str:
        """Validates path, intended to be run in a thread."""
        # Note: Existence check removed here to prevent TOCTOU.
        # It is now handled atomically during the actual file write in utils._save_to_file.
        return validate_path(output_path)

    async def generate_image(
        self, prompt: str, output_path: str, model_id: str, force: bool
    ):
        """Generates an image from a prompt and saves it."""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        output_path = await asyncio.to_thread(self._prepare_output_path, output_path, force)

        try:
            client = await asyncio.to_thread(self.get_client)
        except Exception as e:
            raise ResearchError(f"Client initialization failed: {e}")

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
                            decoded_data = await asyncio.to_thread(base64.b64decode, data)
                            saved = await async_save_binary_to_file(
                                decoded_data,
                                output_path,
                                force,
                                success_prefix="Image saved to",
                            )
                            if not saved:
                                raise ResearchError(f"Failed to save image to {output_path}")
                            return

                raise ResearchError("No image was generated.")
            except Exception as e:
                if isinstance(e, ResearchError):
                    raise e
                raise ResearchError(f"Error generating image: {e}") from e
