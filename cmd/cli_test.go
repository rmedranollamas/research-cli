package cmd

import (
	"bytes"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/db"
	"github.com/spf13/cobra"
)

func setupCmdTestEnv(t *testing.T) (*httptest.Server, string, string) {
	t.Helper()
	db.ResetDBForTesting()

	workspace := t.TempDir()
	dbPath := filepath.Join(t.TempDir(), "history.db")

	oldWorkspace := config.WorkspaceDir
	oldDBPath := config.DbPath
	oldBaseURL := config.GeminiApiBaseUrl

	config.WorkspaceDir = workspace
	config.DbPath = dbPath

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "/v1alpha/interactions") && r.Method == "POST" {
			if strings.Contains(r.URL.RawQuery, "alt=sse") {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte("data: {\"interaction\":{\"id\":\"cmd-inter-1\"},\"delta\":{\"type\":\"text\",\"text\":\"CLI report output\"}}\n"))
				return
			}
			// Image generation or JSON POST
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"outputs":[{"type":"image","data":"aGVsbG8="}]}`))
			return
		}
		if strings.Contains(r.URL.Path, "/v1alpha/interactions/status-id") {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"COMPLETED","outputs":[{"text":"status report text"}]}`))
			return
		}
		w.WriteHeader(http.StatusOK)
	}))

	config.GeminiApiBaseUrl = ts.URL
	t.Setenv(config.GeminiApiKeyVar, "test-api-key")

	// Ensure PersistentPreRun uses our test baseURL
	cobraPreRun := rootCmd.PersistentPreRun
	rootCmd.PersistentPreRun = func(cmd *cobra.Command, args []string) {
		if cobraPreRun != nil {
			cobraPreRun(cmd, args)
		}
		config.GeminiApiBaseUrl = ts.URL
	}

	// Make current working directory equal to workspace for relative path saving in tests
	oldWd, err := os.Getwd()
	if err == nil {
		_ = os.Chdir(workspace)
	}

	t.Cleanup(func() {
		ts.Close()
		db.ResetDBForTesting()
		config.WorkspaceDir = oldWorkspace
		config.DbPath = oldDBPath
		config.GeminiApiBaseUrl = oldBaseURL
		rootCmd.PersistentPreRun = cobraPreRun
		if oldWd != "" {
			_ = os.Chdir(oldWd)
		}
	})

	return ts, workspace, dbPath
}

func TestRootCmdVersion(t *testing.T) {
	buf := new(bytes.Buffer)
	rootCmd.SetOut(buf)
	rootCmd.SetErr(buf)
	rootCmd.SetArgs([]string{"--version"})

	oldVersion := version
	version = "1.2.3"
	defer func() { version = oldVersion }()

	err := rootCmd.Execute()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestRootCmdDefaultQuery(t *testing.T) {
	_, workspace, _ := setupCmdTestEnv(t)
	_ = workspace

	rootCmd.SetArgs([]string{"quantum computing"})
	err := rootCmd.Execute()
	if err != nil {
		t.Fatalf("rootCmd default query error: %v", err)
	}
}

func TestRunCmd(t *testing.T) {
	_, workspace, _ := setupCmdTestEnv(t)
	outPath := "run_report.md"

	t.Run("basic run command with output flag", func(t *testing.T) {
		rootCmd.SetArgs([]string{"run", "deep learning query", "-o", outPath, "--force", "--plan", "--vis", "-v"})
		err := rootCmd.Execute()
		if err != nil {
			t.Fatalf("run command error: %v", err)
		}
		saved, err := os.ReadFile(filepath.Join(workspace, outPath))
		if err != nil {
			t.Fatalf("failed to read saved report: %v", err)
		}
		if string(saved) != "CLI report output" {
			t.Fatalf("saved report = %q, want 'CLI report output'", string(saved))
		}
	})

	t.Run("run command missing API key", func(t *testing.T) {
		t.Setenv(config.GeminiApiKeyVar, "")
		rootCmd.SetArgs([]string{"run", "query without key"})
		err := rootCmd.Execute()
		if err == nil {
			t.Fatal("expected error when API key is missing, got nil")
		}
	})
}

func TestSearchCmd(t *testing.T) {
	_, workspace, _ := setupCmdTestEnv(t)
	outPath := "search_report.md"

	t.Run("search command success with output", func(t *testing.T) {
		rootCmd.SetArgs([]string{"search", "fast search query", "-o", outPath, "-f"})
		err := rootCmd.Execute()
		if err != nil {
			t.Fatalf("search command error: %v", err)
		}
		saved, err := os.ReadFile(filepath.Join(workspace, outPath))
		if err != nil {
			t.Fatalf("failed to read saved search report: %v", err)
		}
		if string(saved) != "CLI report output" {
			t.Fatalf("saved report = %q, want 'CLI report output'", string(saved))
		}
	})
}

func TestStatusCmd(t *testing.T) {
	setupCmdTestEnv(t)

	rootCmd.SetArgs([]string{"status", "status-id"})
	err := rootCmd.Execute()
	if err != nil {
		t.Fatalf("status command error: %v", err)
	}
}

func TestShowCmd(t *testing.T) {
	_, workspace, _ := setupCmdTestEnv(t)

	reportText := "DB saved report"
	taskID, err := db.SaveTask("show query", "model-x", nil, nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := db.UpdateTask(taskID, "COMPLETED", &reportText, nil); err != nil {
		t.Fatal(err)
	}

	t.Run("show existing task", func(t *testing.T) {
		outPath := "show_report.md"
		rootCmd.SetArgs([]string{"show", fmt.Sprintf("%d", taskID), "-o", outPath, "-f"})
		err := rootCmd.Execute()
		if err != nil {
			t.Fatalf("show command error: %v", err)
		}
		saved, err := os.ReadFile(filepath.Join(workspace, outPath))
		if err != nil {
			t.Fatal(err)
		}
		if string(saved) != reportText {
			t.Fatalf("saved report = %q, want %q", string(saved), reportText)
		}
	})

	t.Run("show non-existent task", func(t *testing.T) {
		rootCmd.SetArgs([]string{"show", "999999"})
		err := rootCmd.Execute()
		if err == nil {
			t.Fatal("expected error for non-existent task, got nil")
		}
		if !strings.Contains(err.Error(), "task not found") {
			t.Fatalf("unexpected error message: %v", err)
		}
	})

	t.Run("show invalid task ID", func(t *testing.T) {
		rootCmd.SetArgs([]string{"show", "invalid-id"})
		err := rootCmd.Execute()
		if err == nil {
			t.Fatal("expected error for invalid task ID, got nil")
		}
		if !strings.Contains(err.Error(), "invalid task ID") {
			t.Fatalf("unexpected error message: %v", err)
		}
	})
}

func TestListCmd(t *testing.T) {
	setupCmdTestEnv(t)

	_, err := db.SaveTask("list query 1", "model-1", nil, nil)
	if err != nil {
		t.Fatal(err)
	}

	rootCmd.SetArgs([]string{"list", "-n", "5"})
	err = rootCmd.Execute()
	if err != nil {
		t.Fatalf("list command error: %v", err)
	}
}

func TestGenerateImageCmd(t *testing.T) {
	_, workspace, _ := setupCmdTestEnv(t)
	outPath := "test_generated.png"

	rootCmd.SetArgs([]string{"generate-image", "a futuristic city", "-o", outPath, "-f"})
	err := rootCmd.Execute()
	if err != nil {
		t.Fatalf("generate-image command error: %v", err)
	}

	got, err := os.ReadFile(filepath.Join(workspace, outPath))
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "hello" {
		t.Fatalf("generated image content = %q, want 'hello'", string(got))
	}
}
