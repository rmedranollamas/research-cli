# Research CLI Instruction Manual

Research CLI is a specialized tool for performing deep research using the Gemini Deep Research Agent. It provides a real-time, streaming interface in your terminal.

## Table of Contents

1. [Prerequisites](#prerequisites)
1. [Installation](#installation)
1. [Configuration](#configuration)
1. [Basic Usage](#basic-usage)
1. [Advanced Usage](#advanced-usage)
1. [Architecture & Workflow](#architecture--workflow)
1. [Development & Building](#development--building)
1. [Troubleshooting](#troubleshooting)

______________________________________________________________________

## Prerequisites

- **API Access**: You must have a Gemini API key with access to the `v1alpha` Interactions API and the `deep-research-pro-preview-12-2025` model.
- **Python**: Version 3.11 or higher (if running from source).
- **Tools**: `uv` is recommended for dependency management.

______________________________________________________________________

## Installation

### 1. As a Gemini CLI Extension (Recommended)

This is the preferred installation method for Gemini CLI users. It avoids a full repository clone and uses pre-built, platform-specific binaries.

```bash
gemini extensions install rmedranollamas/research-cli
```

The Gemini CLI will automatically detect your platform and download the corresponding asset (e.g., `linux.arm64.research-cli.tar.gz`) from our latest GitHub Release.

### 2. Quick Install (Stand-alone Binary)

If you are not using the Gemini CLI, you can install the stand-alone binary using our installation script:

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
# Review the script's contents
less install.sh
chmod +x install.sh
./install.sh
```

### 3. From Source (Recommended for Developers)

1. Clone the repository.
1. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
1. Sync dependencies:
   ```bash
   uv sync
   ```

______________________________________________________________________

## Basic Usage

Research CLI uses subcommands for different actions.

### Start a new research task

```bash
research run "The history of the quantum Zeno effect"
```

If running from source:

```bash
uv run research run "Your query here"
```

### List recent tasks

```bash
research list
```

### Show a specific report

```bash
research show <ID>
```

______________________________________________________________________

## Configuration

- **API Key**: Requires `RESEARCH_GEMINI_API_KEY` environment variable.
- **Local History**: Tasks are stored in a SQLite database at `~/.research-cli/history.db`.

______________________________________________________________________

## Advanced Usage

### Specifying a Model

You can override the default research model using the `--model` flag:

```bash
research run "Latest advancements in fusion energy" --model "deep-research-pro-preview-12-2025"
```

### Keyboard Interrupts

If you press `Ctrl+C` during research, the CLI will catch the interrupt and exit gracefully. Note that the research task might continue to run on the server side.

______________________________________________________________________

## Architecture & Workflow

The CLI follows a stateless, polling-based architecture:

1. **Submission**: Sends the query to the Gemini Interactions API.
1. **Streaming**: Connects to an SSE (Server-Sent Events) stream to receive "thoughts" (the agent's internal reasoning).
1. **Polling Fallback**: If the stream disconnects before the report is ready, the CLI enters an optimized polling loop with exponential backoff. It starts with a 1-second interval and increases it until the maximum (default 10 seconds) is reached, polling until it reaches a `COMPLETED` state.
1. **Extraction**: Once completed, the CLI extracts the final report from the interaction's output and renders it as Markdown.

______________________________________________________________________

## Development & Building

### Quality Tools

- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Testing**: `PYTHONPATH=. uv run pytest tests/`

### Building the Binary Locally

To generate a standalone executable for your current platform:

```bash
uv run pyinstaller --onefile --name research --hidden-import=rich._unicode_data.unicode17-0-0 --collect-all research_cli run.py
```

The resulting binary will be in the `dist/` directory.

______________________________________________________________________

## Troubleshooting

### "Error: RESEARCH_GEMINI_API_KEY environment variable not set."

Ensure you have exported the key in your current terminal session.

### "No report content received."

This usually happens if the model failed to generate a report or if the interaction state was lost. Check your API usage/quota on the Google AI Studio console.

### "Internal server error" (API 500/503)

The CLI has built-in retry logic for transient upstream server errors. It will automatically wait and retry polling until the service recovers or the task completes.

### "UserWarning: Interactions usage is experimental"

This is a standard warning from the `google-genai` SDK for the `v1alpha` API. It does not affect functionality.
