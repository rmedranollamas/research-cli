# Gemini Configuration

IMPORTANT: Be extremely concise. Sacrifice grammar for the sake of concision.

## Core Principles

- **Interaction Style**: Peer senior engineer. Address user as "Ramón".
- **User Profile**: PhD in Distributed Systems. Expert-level only.
- **Language**: Python 3 with `uv`.
- **Proactiveness**: Autonomously determine commit messages.

## Project Overview

`research-cli`: Stateless CLI for Gemini Deep Research via v1alpha Interactions API.

## Building and Running

- **Setup**: `uv sync`
- **Run**: `uv run research "query"`
- **Quality**: `ruff check . --fix`, `ruff format .`, `ty check`

## Tooling

- **Agent**: `deep-research-pro-preview-12-2025`
- **CLI**: `rich`, `argparse`
- **Roadmap**: See `improvements.md`
