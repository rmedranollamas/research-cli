package config

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
)

var (
	DefaultModelFallback  = "deep-research-preview-04-2026"
	ConfigDir             string
	DbPath                string
	DefaultModel          string
	GeminiApiKeyVar       = "RESEARCH_GEMINI_API_KEY"
	GeminiApiBaseUrl      string
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
	loadDotenv(dotenvPath)

	DbPath = getEnv("RESEARCH_DB_PATH", filepath.Join(ConfigDir, "history.db"))
	DefaultModel = getEnv("RESEARCH_MODEL", DefaultModelFallback)
	GeminiApiBaseUrl = getEnv("GEMINI_API_BASE_URL", "")

	McpServers = nil
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

func loadDotenv(dotenvPath string) {
	lstatInfo, err := os.Lstat(dotenvPath)
	if err != nil || !lstatInfo.Mode().IsRegular() {
		return
	}

	f, err := os.Open(dotenvPath)
	if err != nil {
		return
	}
	defer f.Close()

	fInfo, err := f.Stat()
	if err != nil || !fInfo.Mode().IsRegular() || !os.SameFile(fInfo, lstatInfo) {
		return
	}

	// Attempt to set permissions to 0600 directly on the file descriptor to avoid TOCTOU/symlink races
	_ = f.Chmod(0600)

	envMap, err := godotenv.Parse(f)
	if err != nil {
		return
	}

	for k, v := range envMap {
		if _, exists := os.LookupEnv(k); !exists {
			_ = os.Setenv(k, v)
		}
	}
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
