package config

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
)

var (
	ConfigDir             string
	DbPath                string
	DefaultModel          string
	GeminiApiKeyVar       = "RESEARCH_GEMINI_API_KEY"
	McpServers            []string
	QueryTruncationLength = 50
	RecentTasksLimit      = 20
	PollIntervalDefault   = 10.0
	WorkspaceDir          string
)

func Load() {
	home, err := os.UserHomeDir()
	if err != nil {
		home = os.Getenv("HOME") // Fallback
	}
	defaultConfigDir := filepath.Join(home, ".research-cli")
	ConfigDir = getEnv("RESEARCH_CONFIG_DIR", defaultConfigDir)

	dotenvPath := filepath.Join(ConfigDir, ".env")
	if _, err := os.Stat(dotenvPath); err == nil {
		// Attempt to set permissions to 0o600 if possible, ignoring errors
		_ = os.Chmod(dotenvPath, 0600)
		_ = godotenv.Load(dotenvPath)
	}

	DbPath = getEnv("RESEARCH_DB_PATH", filepath.Join(ConfigDir, "history.db"))
	DefaultModel = getEnv("RESEARCH_MODEL", "deep-research-preview-04-2026")

	mcpServersRaw := getEnv("RESEARCH_MCP_SERVERS", "")
	if mcpServersRaw != "" {
		parts := strings.Split(mcpServersRaw, ",")
		for _, s := range parts {
			trimmed := strings.TrimSpace(s)
			if trimmed != "" {
				McpServers = append(McpServers, trimmed)
			}
		}
	}

	cwd, _ := os.Getwd()
	WorkspaceDir = getEnv("RESEARCH_WORKSPACE", cwd)
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
