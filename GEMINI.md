# Gemini Configuration & Technical Details

`research-cli`: A specialized, stateful CLI for Gemini Deep Research and multimodal interactions.

## Architecture

### Agents & APIs

- **Deep Research**: Uses the `deep-research-pro-preview-12-2025` model via the **Gemini v1alpha Interactions API**. This allows for long-running research tasks with multi-step reasoning and tool use.
- **Multimodal Support**: Supports `IMAGE`, `TEXT`, and `PDF` (via `Files API`) modalities.
- **Stateful Continuity**: Supports server-side state via `previous_interaction_id`, enabling multi-turn conversations without re-sending full history.

### Gemini CLI Extension

The repository includes a `gemini-extension.json` manifest, allowing it to be used as an extension for the [Gemini CLI](https://geminicli.com/).

- **Slash Commands**: Supports `/research` via `commands/research.toml`.
- **Skills**: Exposes the `gemini-research` skill via `skills/gemini-research/SKILL.md`.

### Performance Optimizations

- **Lazy Loading**: Heavy dependencies such as `google-genai` and `rich` are lazily imported only when needed.
- **Optimized Polling**: When the stream ends before completion, the CLI uses an exponential backoff strategy (starting at 1s, increasing by 1.5x up to `RESEARCH_POLL_INTERVAL`).
- **Security**: Disables console markup (`markup=False`) when printing untrusted LLM content via `rich` to prevent injection.

### Database Architecture

- **SQLite Backend**: Task history and reports are stored in a local SQLite database (default: `~/.research-cli/history.db`).
- **Schema**:
  - The `research_tasks` table stores query details, model information, interaction IDs, and final reports.
  - An index `idx_research_tasks_created_at` optimizes the performance of listing recent tasks.

## Key Features

- **Local File Context**: Support for uploading local files (PDF, TXT, images) to the Files API and using them as research context.
- **Grounding & Search**: Integrated Google Search grounding for both deep research (`run`) and fast search (`search`) commands.
- **MCP Integration**: Supports remote Model Context Protocol (MCP) servers via the `RESEARCH_MCP_SERVERS` environment variable.
- **Image Generation**: Direct image generation via the `generate-image` command using the `IMAGE` modality.

## Building and Running

- **Setup**: `uv sync`
- **Run Deep Research**: `uv run research run "query" [--file path] [--url url]`
- **Fast Search**: `uv run research search "query" [--model gemini-2.0-flash]`
- **Status Check**: `uv run research status <interaction_id>`
- **Generate Image**: `uv run research generate-image "prompt" -o out.png`
- **Test**: `uv run pytest tests/`
- **Quality**: `uv run ruff check . --fix` and `uv run ruff format .`

## Tooling

- **Language**: Python 3.11+ (managed via `uv`)
- **CLI Framework**: `argparse` with `rich` for formatting.
- **SDK**: `google-genai` (Interactions API).

## Installer & Security

The `install.sh` script includes:

- **Piping Protection**: Blocks direct piping to shell.
- **Integrity Verification**: Verifies SHA256 hashes against `checksums.txt` from the official release.
