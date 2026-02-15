# Research CLI

Stateless CLI for Gemini Deep Research and Deep Thinking.

Refer to the [Instruction Manual](MANUAL.md) for detailed setup and usage guides.

## Installation

### Quick Install (Binary)

The installation script securely downloads the latest release binary for your platform and verifies its integrity using SHA256 checksums.

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

Set your `GEMINI_API_KEY` and run a research task:

```bash
export GEMINI_API_KEY="your-api-key"
uv run research run "Your research query here"
```

### Deep Thinking

You can use the `think` command for models that support internal reasoning:

```bash
uv run research think "Your complex question here"
```

If installed via the script or running via `uv run`, you can also use the `think` alias directly:

```bash
uv run think "Your complex question here"
```

### Managing Tasks

List past research and thinking tasks:

```bash
uv run research list
```

Show a specific report from history:

```bash
uv run research show <ID>
```

The CLI will stream the agent's reasoning (thoughts) in real-time and then display the final report in Markdown.

## Configuration

The CLI can be configured via environment variables:

- `GEMINI_API_KEY`: (Required) Your Google Gemini API key.
- `RESEARCH_MODEL`: Gemini model for research (default: `deep-research-pro-preview-12-2025`).
- `THINK_MODEL`: Gemini model for thinking (default: `gemini-2.0-flash-thinking-exp`).
- `RESEARCH_DB_PATH`: Path to the SQLite history database (default: `~/.research-cli/history.db`).
- `RESEARCH_POLL_INTERVAL`: Interval in seconds for polling interaction status (default: `10`).
- `GEMINI_API_BASE_URL`: Optional custom base URL for the Gemini API.

## Agent Skill

A [specification-compliant](https://agentskills.io/) agent skill is included in `skills/gemini-research/`. This allows AI agents to learn how to interact with this CLI autonomously.

## Development

- **Linting & Fixing**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Testing**: `PYTHONPATH=. uv run pytest tests/`
