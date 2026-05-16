# Research CLI Manual

Research CLI is a Go-based terminal tool for Gemini Deep Research, fast grounded search, image generation, and local task history through SQLite.

## Prerequisites

- Gemini API key with access to the v1alpha Interactions API.
- Go 1.24 or newer if building from source.

Default model and agent strings:

- Deep Research: `deep-research-preview-04-2026`
- Deep Research Max: `deep-research-max-preview-04-2026`
- Fast Search: `gemini-3-flash-preview`
- Image Generation: `gemini-3-pro-image-preview`

## Installation

### Gemini CLI Extension

```bash
gemini extensions install rmedranollamas/research-cli
```

### Standalone Binary

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
chmod +x install.sh
./install.sh
```

### Build From Source

```bash
git clone https://github.com/rmedranollamas/research-cli.git
cd research-cli
go build -o research .
./research --version
```

## Configuration

- `RESEARCH_GEMINI_API_KEY`: required Gemini API key.
- `RESEARCH_MODEL`: default Deep Research agent for `run`.
- `RESEARCH_DB_PATH`: SQLite history database path. Defaults to `~/.research-cli/history.db`.
- `RESEARCH_CONFIG_DIR`: configuration directory. Defaults to `~/.research-cli`.
- `RESEARCH_WORKSPACE`: output workspace. Defaults to the current directory.
- `RESEARCH_POLL_INTERVAL`: maximum polling interval in seconds. Defaults to `10`.
- `RESEARCH_MCP_SERVERS`: comma-separated remote MCP server URLs.
- `GEMINI_API_BASE_URL`: optional Gemini API base URL. Non-HTTPS URLs are accepted only for true loopback hosts.

If `RESEARCH_CONFIG_DIR/.env` exists, the CLI loads it before reading configuration values.

## Commands

### Deep Research

```bash
research run "The impact of solid-state batteries on EV adoption"
```

Useful options:

- `--file path`: upload a local file as context.
- `--url https://example.com`: attach a URL as context.
- `--parent <interaction_id>`: continue from a previous interaction.
- `--thinking minimal|low|medium|high`: request a thinking level on supported agents.
- `--visualization`: allow generated visualizations.
- `--no-search`: disable Google Search grounding.
- `--output report.md`: save the report.
- `--force`: overwrite an existing output file.
- `--verbose`: print thought summaries when available.

### Fast Search

```bash
research search "What changed in the latest Gemini Interactions API?"
```

Fast search uses `gemini-3-flash-preview` by default and is intended for concise grounded answers.

### Image Generation

```bash
research generate-image "A clean product render of a brass desk lamp" --output lamp.png
```

### Status And History

```bash
research status <interaction_id>
research list
research show <task_id>
```

The CLI stores task history in SQLite and sets restrictive file permissions on the database.

## Development

```bash
go test ./...
go vet ./...
go build ./...
```

Coverage:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

Release artifacts are built by `.github/workflows/release.yml`. Tagged releases create direct platform binaries plus Gemini extension archives.

## Troubleshooting

### API Key Errors

Set `RESEARCH_GEMINI_API_KEY` or place it in `RESEARCH_CONFIG_DIR/.env`.

### Model Not Found

Use current model strings. Deprecated `gemini-2.0-*` IDs may fail.

### Custom Base URL Rejected

Custom remote endpoints must use HTTPS. Plain HTTP is allowed only for `localhost`, `127.0.0.1`, or `::1`.
