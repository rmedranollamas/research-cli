# Research CLI Instruction Manual

Research CLI is a specialized tool for performing deep research using the Gemini Deep Research Agent. It provides a real-time, streaming interface in your terminal.

## Table of Contents

1. [Prerequisites](#prerequisites)
1. [Installation](#installation)
1. [Configuration](#configuration)
1. [Basic Usage](#basic-usage)
1. [Advanced Usage](#advanced-usage)
1. [Gemini CLI Extension](#gemini-cli-extension)
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

### Quick Install (Recommended for Users)

The easiest way to install the `research` CLI is using our installation script:

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
# Review the script's contents
less install.sh
chmod +x install.sh
./install.sh
```

### From Source (Recommended for Developers)

1. Clone the repository.
1. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
1. Sync dependencies:
   ```bash
   uv sync
   ```

### Using Standalone Binaries

Download the latest binary for your OS and architecture from the [GitHub Releases](https://github.com/rmedranollamas/research-cli/releases) page.

- **Linux x64**: `research-linux-amd64`
- **Linux arm64**: `research-linux-arm64`
- **macOS x64**: `research-darwin-amd64`
- **macOS arm64**: `research-darwin-arm64`

Rename the binary to `research` and move it to your PATH (e.g., `/usr/local/bin`).

### Gemini CLI Extension (Modern)

If you have the [Gemini CLI](https://geminicli.com/) installed, you can add this project as an extension:

```bash
gemini extensions install https://github.com/rmedranollamas/research-cli
```

______________________________________________________________________

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

______________________________________________________________________

## Configuration

Research CLI can be configured via environment variables:

- **`RESEARCH_GEMINI_API_KEY`**: (Required) Your Google Gemini API key.
- **`RESEARCH_MODEL`**: Gemini model for research (default: `deep-research-pro-preview-12-2025`).
- **`RESEARCH_CONFIG_DIR`**: Root directory for configuration and history (default: `~/.research-cli`).
- **`RESEARCH_DB_PATH`**: Path to the SQLite history database (default: `$RESEARCH_CONFIG_DIR/history.db`).
- **`RESEARCH_POLL_INTERVAL`**: Maximum interval in seconds for polling interaction status (default: `10`).
- **`GEMINI_API_BASE_URL`**: Optional custom base URL for the Gemini API.

______________________________________________________________________

## Advanced Usage

### Quick Research Shortcut

The `think` entry point allows you to start a research task without the `run` subcommand:

```bash
uv run think "Latest advancements in fusion energy"
```

This is equivalent to `uv run research run "Latest advancements in fusion energy"`.

### Specifying a Model

You can override the default research model using the `--model` flag:

```bash
uv run research run "Latest advancements in fusion energy" --model "deep-research-pro-preview-12-2025"
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
- **Type Checking**: `uv run ty check`

### Building the Binary Locally

To generate a standalone executable for your current platform:

```bash
uv run pyinstaller --onefile --name research run.py
```

The resulting binary will be in the `dist/` directory.

______________________________________________________________________

## Troubleshooting

### "Error: RESEARCH_GEMINI_API_KEY environment variable not set."

Ensure you have exported the key in your current terminal session.

### "No report content received."

This usually happens if the model failed to generate a report or if the interaction state was lost. Check your API usage/quota on the Google AI Studio console.

### "UserWarning: Interactions usage is experimental"

This is a standard warning from the `google-genai` SDK for the `v1alpha` API. It does not affect functionality.

### Interaction Stuck in `IN_PROGRESS`

Deep research can take several minutes. The CLI will continue polling as long as the status is `IN_PROGRESS`.

______________________________________________________________________

## Gemini CLI Extension

This repository is a compliant Gemini CLI extension.

### Installation

```bash
gemini extensions install https://github.com/rmedranollamas/research-cli
```

### Slash Commands

Once installed, the following slash commands are available in your `gemini` CLI:

- **`/research <query>`**: Starts a deep research task using the `gemini-research` skill.

### Agent Skills

The extension provides the `gemini-research` skill, which AI agents can use to perform autonomous research tasks.
