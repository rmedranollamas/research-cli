# Research CLI

Stateless CLI for Gemini Deep Research via the v1alpha Interactions API.

Refer to the [Instruction Manual](MANUAL.md) for detailed setup and usage guides.

## Installation

Ensure you have `uv` installed, then sync the project:

```bash
uv sync
```

## Usage

Set your `GEMINI_API_KEY` and run the research command:

```bash
export GEMINI_API_KEY="your-api-key"
uv run research "Your research query here"
```

The CLI will stream the agent's reasoning (thoughts) and then display the final report in Markdown.

## Development

- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Type Checking**: `uv run ty check`