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
	dotenvFile := filepath.Join(configDir, ".env")
	if err := os.WriteFile(dotenvFile, []byte("RESEARCH_MODEL=dotenv-model\n"), 0644); err != nil {
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

	info, err := os.Stat(dotenvFile)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm() != 0600 {
		t.Fatalf("dotenv perm = %o, want 0600", info.Mode().Perm())
	}
}

func TestLoadRejectsSymlinkDotenv(t *testing.T) {
	configDir := t.TempDir()
	targetFile := filepath.Join(t.TempDir(), "target.env")
	if err := os.WriteFile(targetFile, []byte("RESEARCH_MODEL=symlink-model\n"), 0644); err != nil {
		t.Fatal(err)
	}

	symlinkFile := filepath.Join(configDir, ".env")
	if err := os.Symlink(targetFile, symlinkFile); err != nil {
		t.Fatal(err)
	}

	t.Setenv("RESEARCH_CONFIG_DIR", configDir)
	t.Setenv("RESEARCH_DB_PATH", filepath.Join(t.TempDir(), "history.db"))
	t.Setenv("RESEARCH_WORKSPACE", t.TempDir())
	if err := os.Unsetenv("RESEARCH_MODEL"); err != nil {
		t.Fatal(err)
	}

	McpServers = nil
	Load()

	if DefaultModel == "symlink-model" {
		t.Fatalf("DefaultModel loaded value from symlinked .env file")
	}

	// Verify target file permissions were not changed to 0600
	info, err := os.Stat(targetFile)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm() == 0600 {
		t.Fatalf("target file permissions were changed via symlink")
	}
}

func TestGetEnv(t *testing.T) {
	t.Run("returns env var value when set", func(t *testing.T) {
		t.Setenv("TEST_GETENV_VAR", "value123")
		got := getEnv("TEST_GETENV_VAR", "fallback")
		if got != "value123" {
			t.Errorf("getEnv() = %q, want %q", got, "value123")
		}
	})

	t.Run("returns fallback when key is not set", func(t *testing.T) {
		key := "TEST_GETENV_UNSET_VAR_999"
		os.Unsetenv(key)
		got := getEnv(key, "default_fallback")
		if got != "default_fallback" {
			t.Errorf("getEnv() = %q, want %q", got, "default_fallback")
		}
	})

	t.Run("returns empty string when key is set to empty string", func(t *testing.T) {
		t.Setenv("TEST_GETENV_VAR_EMPTY", "")
		got := getEnv("TEST_GETENV_VAR_EMPTY", "fallback")
		if got != "" {
			t.Errorf("getEnv() = %q, want %q", got, "")
		}
	})
}
