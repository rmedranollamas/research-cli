# Gemini Configuration And Technical Details

`research-cli` is a Go CLI for Gemini Deep Research and multimodal interactions.

## Architecture

- Deep Research uses `deep-research-preview-04-2026` through the Gemini v1alpha Interactions API.
- Max Deep Research can be selected with `deep-research-max-preview-04-2026`.
- Fast search uses `gemini-3-flash-preview`.
- Image generation uses `gemini-3-pro-image-preview`.
- Long-running interactions stream over SSE, then fall back to polling if the stream ends before a report is available.
- Local task history is stored in SQLite at `~/.research-cli/history.db` by default.

## Gemini CLI Extension

- Manifest: `gemini-extension.json`
- Slash command: `commands/research.toml`
- Skill: `skills/gemini-research/SKILL.md`
- Release archives place the platform binary at `skills/gemini-research/scripts/research`.

## Security Notes

- `RESEARCH_GEMINI_API_KEY` is passed only to Gemini API requests.
- Custom remote API base URLs must use HTTPS. HTTP is accepted only for real loopback hosts.
- Workspace path validation rejects parent traversal and symlink output overwrites.
- Untrusted streamed model text is stripped of terminal control sequences before printing.
- The SQLite history database is created with `0600` permissions.

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

## Release

Pushing a `v*` tag runs `.github/workflows/release.yml`, which builds Go binaries for Linux and macOS on amd64 and arm64, packages Gemini extension archives, and publishes checksums.
