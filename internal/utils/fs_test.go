package utils

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/research-cli/internal/config"
)

func TestValidatePath(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	t.Run("empty path", func(t *testing.T) {
		_, err := ValidatePath("")
		if err == nil {
			t.Fatal("expected error for empty path, got nil")
		}
	})

	t.Run("relative path inside workspace", func(t *testing.T) {
		relPath := filepath.Join("sub", "file.txt")
		want := filepath.Join(workspace, relPath)
		got, err := ValidatePath(relPath)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != want {
			t.Fatalf("ValidatePath() = %q, want %q", got, want)
		}
	})

	t.Run("absolute path inside workspace", func(t *testing.T) {
		absPath := filepath.Join(workspace, "sub", "file.txt")
		got, err := ValidatePath(absPath)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != absPath {
			t.Fatalf("ValidatePath() = %q, want %q", got, absPath)
		}
	})

	t.Run("path traversal rejected", func(t *testing.T) {
		if _, err := ValidatePath(filepath.Join("..", "outside.txt")); err == nil {
			t.Fatal("ValidatePath accepted parent traversal")
		}
	})

	t.Run("dot dot prefixed name inside workspace allowed", func(t *testing.T) {
		want := filepath.Join(workspace, "..cache", "out.txt")
		got, err := ValidatePath(filepath.Join(".", "..cache", "out.txt"))
		if err != nil {
			t.Fatalf("ValidatePath returned error for valid workspace path: %v", err)
		}
		if got != want {
			t.Fatalf("ValidatePath() = %q, want %q", got, want)
		}
	})
}

func TestSanitizePath(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	t.Run("empty path", func(t *testing.T) {
		if got := SanitizePath(""); got != "" {
			t.Fatalf("SanitizePath(\"\") = %q, want empty string", got)
		}
	})

	t.Run("path inside workspace", func(t *testing.T) {
		fullPath := filepath.Join(workspace, "dir", "file.txt")
		want := filepath.Join("dir", "file.txt")
		if got := SanitizePath(fullPath); got != want {
			t.Fatalf("SanitizePath(%q) = %q, want %q", fullPath, got, want)
		}
	})

	t.Run("path outside workspace returns base name", func(t *testing.T) {
		outsidePath := filepath.Join(t.TempDir(), "outside", "file.txt")
		want := "file.txt"
		if got := SanitizePath(outsidePath); got != want {
			t.Fatalf("SanitizePath(%q) = %q, want %q", outsidePath, got, want)
		}
	})
}

func TestSaveToFile(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	t.Run("save new file", func(t *testing.T) {
		path := filepath.Join(workspace, "new.txt")
		content := []byte("hello world")
		if err := SaveToFile(content, path, false); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		got, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if string(got) != string(content) {
			t.Fatalf("file content = %q, want %q", string(got), string(content))
		}
	})

	t.Run("overwrite existing file with force=true", func(t *testing.T) {
		path := filepath.Join(workspace, "force.txt")
		if err := os.WriteFile(path, []byte("old"), 0644); err != nil {
			t.Fatal(err)
		}
		content := []byte("new content")
		if err := SaveToFile(content, path, true); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		got, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if string(got) != string(content) {
			t.Fatalf("file content = %q, want %q", string(got), string(content))
		}
	})

	t.Run("reject existing file without force", func(t *testing.T) {
		path := filepath.Join(workspace, "existing.txt")
		if err := os.WriteFile(path, []byte("original"), 0644); err != nil {
			t.Fatal(err)
		}
		err := SaveToFile([]byte("new"), path, false)
		if err == nil || !strings.Contains(err.Error(), "already exists") {
			t.Fatalf("SaveToFile error = %v, want already exists", err)
		}
	})

	t.Run("reject symlink overwrite", func(t *testing.T) {
		outside := t.TempDir()
		target := filepath.Join(outside, "target.txt")
		if err := os.WriteFile(target, []byte("original"), 0644); err != nil {
			t.Fatal(err)
		}
		link := filepath.Join(workspace, "output.txt")
		if err := os.Symlink(target, link); err != nil {
			t.Skipf("symlinks unavailable: %v", err)
		}
		err := SaveToFile([]byte("new"), link, true)
		if err == nil {
			t.Fatal("SaveToFile succeeded; want symlink overwrite rejection")
		}
		data, err := os.ReadFile(target)
		if err != nil {
			t.Fatal(err)
		}
		if string(data) != "original" {
			t.Fatalf("target was overwritten: got %q", string(data))
		}
	})
}

func TestGetApiKey(t *testing.T) {
	t.Run("returns API key when set", func(t *testing.T) {
		expectedKey := "test-gemini-api-key-12345"
		t.Setenv(config.GeminiApiKeyVar, expectedKey)

		key, err := GetApiKey()
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if key != expectedKey {
			t.Errorf("GetApiKey() = %q, want %q", key, expectedKey)
		}
	})

	t.Run("returns error when unset", func(t *testing.T) {
		t.Setenv(config.GeminiApiKeyVar, "")

		key, err := GetApiKey()
		if err == nil {
			t.Fatal("expected error when API key is unset, got nil")
		}
		if key != "" {
			t.Errorf("GetApiKey() = %q, want empty string", key)
		}
		expectedErrSubstr := config.GeminiApiKeyVar + " environment variable not set"
		if !strings.Contains(err.Error(), expectedErrSubstr) {
			t.Errorf("error %q does not contain %q", err.Error(), expectedErrSubstr)
		}
	})
}
