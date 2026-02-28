# Research CLI

Stateless CLI for Gemini Deep Research.

Refer to the [Instruction Manual](MANUAL.md) for detailed setup and usage guides.

## Installation

### As a Gemini CLI Extension (Recommended)

This is the fastest and most efficient way to install the tool. The Gemini CLI will automatically fetch the optimized, platform-specific binary from our latest release.

```bash
gemini extensions install rmedranollamas/research-cli
```

### Quick Install (Stand-alone Binary)

Alternatively, you can use the installation script to download and verify the stand-alone binary:

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
# Review the script's contents
less install.sh
chmod +x install.sh
./install.sh
```

### From Source

Ensure you have `uv` installed, then sync the project:

```bash
uv sync
```

## Usage

Set your `RESEARCH_GEMINI_API_KEY` and run a research task:

```bash
export RESEARCH_GEMINI_API_KEY="your-api-key"
research run "How does quantum entanglement work?"
```

If running from source:

```bash
uv run research run "How does quantum entanglement work?"
```

### Key Commands

- **Deep Research**: `research run "query"` - Multi-step, long-running research.
- **Fast Search**: `research search "query"` - Quick, grounded answers using `gemini-2.0-flash`.
- **Status**: `research status <interaction_id>` - Check progress of a background task.
- **Image Generation**: `research generate-image "prompt" -o robot.png` - Generate AI images.
- **List Tasks**: `research list` - View recent task history.
- **Show Task**: `research show <ID>` - Display a specific report from history.

### Context & Options

- **Files**: `--file path/to/file.pdf` - Use local files as context.
- **URLs**: `--url https://example.com` - Use web pages as context.
- **Verbose**: `-v` or `--verbose` - See the agent's real-time "thoughts" and reasoning.
- **Thinking**: `--thinking [minimal|low|medium|high]` - Control reasoning depth (on supported models).

## Configuration

The CLI can be configured via environment variables:

- `RESEARCH_GEMINI_API_KEY`: (Required) Your Google Gemini API key.
- `RESEARCH_MODEL`: Gemini model for research (default: `deep-research-pro-preview-12-2025`).
- `RESEARCH_DB_PATH`: Path to the SQLite history database (default: `~/.research-cli/history.db`).
- `RESEARCH_POLL_INTERVAL`: Maximum interval in seconds for polling interaction status (default: `10`).
- `RESEARCH_MCP_SERVERS`: Comma-separated list of MCP server URLs for extended tool use.
- `GEMINI_API_BASE_URL`: Optional custom base URL for the Gemini API.

## Agent Skill

A [specification-compliant](https://agentskills.io/) agent skill is included in `skills/gemini-research/`. This allows AI agents to learn how to interact with this CLI autonomously.

## Development

- **Linting & Fixing**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Testing**: `uv run pytest tests/`
