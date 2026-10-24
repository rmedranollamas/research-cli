# Agent Notes

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

The workspace has used Go `1.26.3`. Keep the `go` directive in `go.mod` aligned
with the intended release toolchain; the release workflow uses
`actions/setup-go` with `go-version-file: go.mod`.

Coverage:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

## Release

Pushing a `v*` tag runs `.github/workflows/release.yml`, which builds Go binaries for Linux and macOS on amd64 and arm64, packages Gemini extension archives, and publishes checksums.

### Release Checklist

1. **Pre-flight checks**:
   Ensure the working tree is clean, synced with upstream, properly formatted, and passing tests:

   ```bash
   git status
   git pull
   gofmt -l .
   go vet ./...
   go test ./...
   ```

1. **Version bump**:
   Update the version string to `X.Y.Z` in:

   - `cmd/root.go` (`var version = "X.Y.Z"`)
   - `gemini-extension.json` (`"version": "X.Y.Z"`)

1. **Commit & push**:
   Stage changes, commit, and push to `main`:

   ```bash
   git add cmd/root.go gemini-extension.json AGENTS.md
   git commit -m "bump version to X.Y.Z"
   git push origin main
   ```

1. **Tag creation & push**:
   Create an annotated tag and push it to trigger the release workflow:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

1. **Monitor workflow**:
   Watch the release workflow execution until completion:

   ```bash
   gh run watch
   ```

1. **Post-release verification protocol**:
   Verify release assets, checksums, and extracted binary:

   ```bash
   gh release view vX.Y.Z
   mkdir -p /tmp/test-release
   gh release download vX.Y.Z -D /tmp/test-release
   cd /tmp/test-release
   sha256sum -c checksums.txt --ignore-missing
   tar -xzf research-cli_vX.Y.Z_linux_amd64.tar.gz
   ./skills/gemini-research/scripts/research --version
   ```

## Dependency Updates

Use the Go toolchain to update the module graph, then run `go mod tidy` and the
normal test/vet/build checks. Do not blindly force every dependency to
`@latest`: some valid resolved versions are pseudo-versions newer than the
latest tagged release, and forcing `@latest` can downgrade or break the graph.
