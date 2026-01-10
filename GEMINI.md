# Gemini Configuration

`research-cli`: Stateless CLI for Gemini Deep Research via v1alpha Interactions API.

## Building and Running

- **Setup**: `uv sync`
- **Run**: `uv run research "query"`
- **Test**: `PYTHONPATH=. uv run pytest tests/`
- **Quality**: `ruff check . --fix`, `ruff format .`, `ty check`

## Tooling

- **Language**: Python 3 (`uv`)
- **Agent**: `deep-research-pro-preview-12-2025`
- **CLI**: `rich`, `argparse`
- **Roadmap**: See `improvements.md`