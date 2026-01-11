# Research CLI

Stateless CLI for Gemini Deep Research via the v1alpha Interactions API.

Refer to the [Instruction Manual](MANUAL.md) for detailed setup and usage guides.

## Installation

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

You can also list past research:
```bash
uv run research list
```

The CLI will stream the agent's reasoning (thoughts) and then display the final report in Markdown.

## Agent Skill

A [specification-compliant](https://agentskills.io/) agent skill is included in `skills/gemini-research/`. This allows AI agents to learn how to interact with this CLI autonomously.

## Development

- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Type Checking**: `uv run ty check`