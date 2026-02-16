# Gemini Configuration & Technical Details

`research-cli`: A specialized, stateless CLI for Gemini Deep Research and Deep Thinking.

## Architecture

### Agents & APIs

- **Deep Research**: Uses the `deep-research-pro-preview-12-2025` model via the **Gemini v1alpha Interactions API**. This allows for long-running research tasks with multi-step reasoning and tool use.
- **Deep Thinking**: Uses the `gemini-2.0-flash-thinking-exp` model via the **Gemini v1alpha Generate Content API** (default). This supports internal reasoning (thoughts) that are streamed to the terminal.

### Performance Optimizations

- **Lazy Loading**: Heavy dependencies such as `google-genai` and `rich` are lazily imported only when needed. This reduces CLI startup latency by approximately 90% for non-execution commands like `--help`, `version`, or `list`.
- **Asynchronous I/O**: The CLI uses `asyncio` for streaming events. Database updates during research streams are offloaded to background tasks to prevent blocking the event processing loop.
- **Optimized Polling**: When the stream ends before completion, the CLI uses an exponential backoff strategy for polling (starting at 1s, increasing by 1.5x up to the configured `RESEARCH_POLL_INTERVAL`). This improves responsiveness for fast-completing tasks.

### Database Architecture

- **SQLite Backend**: Task history and reports are stored in a local SQLite database (default: `~/.research-cli/history.db`).
- **Schema**:
    - The `research_tasks` table stores query details, model information, interaction IDs, and final reports.
    - An index `idx_research_tasks_created_at` is used to optimize the performance of listing recent tasks.
- **Lazy Initialization**: The database and its schema are initialized lazily upon the first write operation, using thread-safe locking mechanisms.
- **Security**:
    - The database directory is created with `0700` permissions.
    - The database file is created with `0600` permissions.
    - The CLI performs permission checks and safe `chmod` operations to ensure that history data remains accessible only to the user.

## Building and Running

- **Setup**: `uv sync`
- **Run Research**: `uv run research run "query"`
- **Run Thinking**: `uv run research think "query"`
- **Test**: `PYTHONPATH=. uv run pytest tests/`
- **Quality**: `uv run ruff check . --fix` and `uv run ruff format .`

## Tooling

- **Language**: Python 3.11+ (managed via `uv`)
- **CLI Framework**: `argparse` with `rich` for terminal formatting and progress visualization.
- **SDK**: `google-genai` (Interaction and Generate Content APIs).

## Installer & Security

The `install.sh` script includes several security features:
- **Piping Protection**: Blocks direct piping to a shell to encourage script review.
- **Integrity Verification**: Downloads a `checksums.txt` file from the official GitHub release and verifies the binary's SHA256 hash before installation.
- **Buffered Calculation**: Uses buffered reading in Python to calculate checksums efficiently for any file size.
