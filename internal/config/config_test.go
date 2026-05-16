package config

import (
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestLoadAppliesEnvironmentOverrides(t *testing.T) {
	configDir := t.TempDir()
	workspace := t.TempDir()
	dbPath := filepath.Join(t.TempDir(), "history.db")

	t.Setenv("RESEARCH_CONFIG_DIR", configDir)
	t.Setenv("RESEARCH_DB_PATH", dbPath)
	t.Setenv("RESEARCH_MODEL", "custom-model")
	t.Setenv("GEMINI_API_BASE_URL", "https://proxy.example.test")
	t.Setenv("RESEARCH_MCP_SERVERS", "https://mcp-a.example.test, ,https://mcp-b.example.test")
	t.Setenv("RESEARCH_WORKSPACE", workspace)

	McpServers = nil
	Load()

	if ConfigDir != configDir {
		t.Fatalf("ConfigDir = %q, want %q", ConfigDir, configDir)
	}
	if DbPath != dbPath {
		t.Fatalf("DbPath = %q, want %q", DbPath, dbPath)
	}
	if DefaultModel != "custom-model" {
		t.Fatalf("DefaultModel = %q", DefaultModel)
	}
	if GeminiApiBaseUrl != "https://proxy.example.test" {
		t.Fatalf("GeminiApiBaseUrl = %q", GeminiApiBaseUrl)
	}
	if WorkspaceDir != workspace {
		t.Fatalf("WorkspaceDir = %q, want %q", WorkspaceDir, workspace)
	}
	wantServers := []string{"https://mcp-a.example.test", "https://mcp-b.example.test"}
	if !reflect.DeepEqual(McpServers, wantServers) {
		t.Fatalf("McpServers = %#v, want %#v", McpServers, wantServers)
	}
}

func TestLoadReadsDotenv(t *testing.T) {
	configDir := t.TempDir()
	if err := os.WriteFile(filepath.Join(configDir, ".env"), []byte("RESEARCH_MODEL=dotenv-model\n"), 0644); err != nil {
		t.Fatal(err)
	}

	t.Setenv("RESEARCH_CONFIG_DIR", configDir)
	t.Setenv("RESEARCH_DB_PATH", filepath.Join(t.TempDir(), "history.db"))
	t.Setenv("RESEARCH_WORKSPACE", t.TempDir())
	t.Setenv("RESEARCH_MODEL", "")
	if err := os.Unsetenv("RESEARCH_MODEL"); err != nil {
		t.Fatal(err)
	}

	McpServers = nil
	Load()

	if DefaultModel != "dotenv-model" {
		t.Fatalf("DefaultModel = %q, want dotenv-model", DefaultModel)
	}
}
