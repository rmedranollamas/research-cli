# Research CLI

Research CLI is a Go command-line tool for Gemini Deep Research, fast grounded search, image generation, and local research history.

See [MANUAL.md](MANUAL.md) for the full usage guide.

## Installation

### Gemini CLI Extension

```bash
gemini extensions install rmedranollamas/research-cli
```

### Standalone Binary

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh
less install.sh
chmod +x install.sh
./install.sh
```

### From Source

```bash
git clone https://github.com/rmedranollamas/research-cli.git
cd research-cli
go build -o research .
./research --help
```

## Usage

```bash
export RESEARCH_GEMINI_API_KEY="your-api-key"
research run "How does quantum entanglement work?"
```

Key commands:

- `research run "query"`: long-running Deep Research using `deep-research-preview-04-2026`.
- `research search "query"`: quick grounded answers using `gemini-3-flash-preview`.
- `research status <interaction_id>`: poll an existing interaction.
- `research generate-image "prompt" -o image.png`: generate an image using `gemini-3-pro-image-preview`.
- `research list`: view recent local task history.
- `research show <id>`: display a stored report.

## Configuration

- `RESEARCH_GEMINI_API_KEY`: required Gemini API key.
- `RESEARCH_MODEL`: default Deep Research agent for `run`.
- `RESEARCH_DB_PATH`: SQLite history database path. Defaults to `~/.research-cli/history.db`.
- `RESEARCH_WORKSPACE`: workspace for outputs. Defaults to the current directory.
- `RESEARCH_POLL_INTERVAL`: maximum polling interval in seconds. Defaults to `10`.
- `RESEARCH_MCP_SERVERS`: comma-separated remote MCP server URLs.
- `GEMINI_API_BASE_URL`: optional Gemini API base URL. HTTP is allowed only for loopback hosts.

Use `RESEARCH_MODEL=deep-research-max-preview-04-2026` when you want the max Deep Research agent.

## Development

```bash
go test ./...
go vet ./...
go build ./...
```

To inspect test coverage:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

## Agent Skill

The Gemini extension packages `skills/gemini-research/` and `commands/research.toml`, with a platform-specific Go binary placed at `skills/gemini-research/scripts/research`.
