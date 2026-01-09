# Research CLI Instruction Manual

Research CLI is a specialized tool for performing deep research using the Gemini Deep Research Agent. It provides a real-time, streaming interface in your terminal.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [Architecture & Workflow](#architecture--workflow)
7. [Development & Building](#development--building)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites
- **API Access**: You must have a Gemini API key with access to the `v1alpha` Interactions API and the `deep-research-pro-preview-12-2025` model.
- **Python**: Version 3.11 or higher (if running from source).
- **Tools**: `uv` is recommended for dependency management.

---

## Installation

### From Source (Recommended for Developers)
1. Clone the repository.
2. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Sync dependencies:
   ```bash
   uv sync
   ```

### Using Standalone Binaries
Download the latest binary for your OS from the [GitHub Releases](https://github.com/rmedranollamas/research-cli/releases) page.
- **Linux**: `research-ubuntu-latest`
- **macOS**: `research-macos-latest`

Rename the binary to `research` and move it to your PATH (e.g., `/usr/local/bin`).

---

## Basic Usage
Research CLI uses subcommands for different actions.

### Start a new research task
```bash
uv run research run "Your query here"
```

### List recent tasks
```bash
uv run research list
```

### Show a specific report
```bash
uv run research show <ID>
```

---

## Configuration
- **API Key**: Requires `GEMINI_API_KEY` environment variable.
- **Local History**: Tasks are stored in a SQLite database at `~/.research-cli/history.db`.

---

## Advanced Usage

### Specifying a Model
You can override the default Deep Research model using the `--model` flag:
```bash
uv run research "Latest advancements in fusion energy" --model "deep-research-pro-preview-12-2025"
```

### Keyboard Interrupts
If you press `Ctrl+C` during research, the CLI will catch the interrupt and exit gracefully. Note that the research task might continue to run on the server side.

---

## Architecture & Workflow
The CLI follows a stateless, polling-based architecture:
1. **Submission**: Sends the query to the Gemini Interactions API.
2. **Streaming**: Connects to an SSE (Server-Sent Events) stream to receive "thoughts" (the agent's internal reasoning).
3. **Polling Fallback**: If the stream disconnects before the report is ready, the CLI enters a polling loop, checking the interaction status every 10 seconds until it reaches a `COMPLETED` state.
4. **Extraction**: Once completed, the CLI extracts the final report from the interaction's output and renders it as Markdown.

---

## Development & Building

### Quality Tools
- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Type Checking**: `uv run ty check`

### Building the Binary Locally
To generate a standalone executable for your current platform:
```bash
uv run pyinstaller --onefile --name research research.py
```
The resulting binary will be in the `dist/` directory.

---

## Troubleshooting

### "Error: GEMINI_API_KEY environment variable not set."
Ensure you have exported the key in your current terminal session.

### "No report content received."
This usually happens if the model failed to generate a report or if the interaction state was lost. Check your API usage/quota on the Google AI Studio console.

### "UserWarning: Interactions usage is experimental"
This is a standard warning from the `google-genai` SDK for the `v1alpha` API. It does not affect functionality.

### Interaction Stuck in `IN_PROGRESS`
Deep research can take several minutes. The CLI will continue polling as long as the status is `IN_PROGRESS`.
