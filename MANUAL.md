# Research CLI Instruction Manual

Research CLI is a specialized tool for performing deep research, fast grounded searches, and AI-powered image generation using the Gemini Interactions API. It provides a real-time, streaming interface in your terminal.

## Table of Contents

1. [Prerequisites](#prerequisites)
1. [Installation](#installation)
1. [Configuration](#configuration)
1. [Core Commands](#core-commands)
1. [Context & Options](#context--options)
1. [Stateful Research (Continuity)](#stateful-research-continuity)
1. [Architecture & Workflow](#architecture--workflow)
1. [Development & Building](#development--building)
1. [Troubleshooting](#troubleshooting)

______________________________________________________________________

## Prerequisites

- **API Access**: You must have a Gemini API key with access to the `v1alpha` Interactions API.
- **Models**:
  - Deep Research: `deep-research-pro-preview-12-2025`
  - Fast Search: `gemini-2.0-flash` (or newer)
  - Image Gen: `gemini-3-pro-image-preview`
- **Python**: Version 3.11 or higher (if running from source).
- **Tools**: `uv` is recommended for dependency management.

______________________________________________________________________

## Installation

### 1. As a Gemini CLI Extension (Recommended)

This is the preferred installation method for Gemini CLI users. It avoids a full repository clone and uses pre-built, platform-specific binaries.

```bash
gemini extensions install rmedranollamas/research-cli
```

### 2. Quick Install (Stand-alone Binary)

If you are not using the Gemini CLI, you can install the stand-alone binary using our installation script:

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
chmod +x install.sh
./install.sh
```

### 3. From Source (Recommended for Developers)

```bash
git clone https://github.com/rmedranollamas/research-cli.git
cd research-cli
uv sync
```

______________________________________________________________________

## Configuration

The CLI is configured primarily through environment variables:

- `RESEARCH_GEMINI_API_KEY`: (Required) Your Google Gemini API key.
- `RESEARCH_MODEL`: Default model for `run` (default: `deep-research-pro-preview-12-2025`).
- `RESEARCH_DB_PATH`: Path to the SQLite history database (default: `~/.research-cli/history.db`).
- `RESEARCH_POLL_INTERVAL`: Max interval in seconds for polling (default: `10`).
- `RESEARCH_MCP_SERVERS`: Comma-separated list of MCP server URLs (e.g., `http://localhost:8080/mcp`).
- `GEMINI_API_BASE_URL`: Optional custom base URL for the Gemini API.

______________________________________________________________________

## Core Commands

### Deep Research (`run`)

Performs an exhaustive, multi-step research task. It uses grounding, searches, and reasoning to produce a high-quality report.

```bash
research run "The impact of solid-state batteries on the EV industry"
```

### Fast Search (`search`)

A quicker, grounded search command for questions that need immediate, fact-checked answers without full deep research.

```bash
research search "What is the current population of Tokyo?" -v
```

### Status Check (`status`)

If you have an Interaction ID (from a background or previous task), you can poll its current status and retrieve the report if finished.

```bash
research status v1_ChdPdXVpYWNpdkpNMnJrZFVQdXJEVDZBURIXT3V1...
```

### Image Generation (`generate-image`)

Generates an image from a text prompt and saves it locally.

```bash
research generate-image "A futuristic cyberpunk city with neon lights" --output city.png
```

### History Management

- `research list`: Shows the last 20 tasks and their status.
- `research show <ID>`: Displays the full report for a previously completed task.

______________________________________________________________________

## Context & Options

### Multimodal Input

- **Files**: Use `--file` to upload local documents (PDF, TXT, images) as context.
  ```bash
  research run "Summarize the key findings in this report" --file annual_report.pdf
  ```
- **URLs**: Use `--url` to include web pages in the research context.
  ```bash
  research run "Compare these two articles" --url https://site-a.com --url https://site-b.com
  ```

### Reasoning Control

- **Verbose Mode (`-v`)**: Shows the model's internal "Thought Blocks" in real-time. Highly recommended for understanding the research process.
- **Thinking Level**: Use `--thinking [minimal|low|medium|high]` to control the depth of reasoning on supported models.

______________________________________________________________________

## Stateful Research (Continuity)

The CLI supports multi-turn conversations by referencing a "Parent ID". This allows the model to remember previous turns without re-sending the entire history.

1. Start a task and note the **Interaction ID** in the output.
1. Run a follow-up query:
   ```bash
   research run "Can you expand more on the second point?" --parent <PREVIOUS_INTERACTION_ID>
   ```

______________________________________________________________________

## Architecture & Workflow

1. **Submission**: Sends the query to the Gemini Interactions API.
1. **Streaming**: Connects to an SSE stream to receive "thoughts" and partial content.
1. **Polling Fallback**: If the stream disconnects, the CLI enters an exponential backoff polling loop.
1. **Storage**: All queries and final reports are stored in a local SQLite database with `0600` permissions.

______________________________________________________________________

## Development & Building

### Quality Tools

- **Testing**: `uv run pytest tests/`
- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`

### Building the Binary Locally

```bash
uv run pyinstaller --onefile --name research \
  --hidden-import=rich._unicode_data.unicode17-0-0 \
  --collect-all research_cli \
  run.py
```

______________________________________________________________________

## Troubleshooting

### "Invalid content type: document" or "Cannot fetch content"

The Interactions API is experimental. If direct file context fails, ensure your API key has the necessary permissions or try a smaller file.

### "API key expired"

Renew your API key in Google AI Studio.

### "Model not found"

Ensure you are using a supported model ID. For `search`, `gemini-2.0-flash` or newer is required.
