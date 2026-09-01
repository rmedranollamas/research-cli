package agent

import (
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/research-cli/internal/config"
)

func TestNewResearchAgent(t *testing.T) {
	t.Run("valid secure baseURL", func(t *testing.T) {
		agent, err := NewResearchAgent("test-api-key", "https://api.example.com")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if agent == nil {
			t.Fatal("expected agent, got nil")
		}
		if agent.GetClient() == nil {
			t.Fatal("expected non-nil genai.Client from GetClient()")
		}
	})

	t.Run("valid loopback http baseURL", func(t *testing.T) {
		agent, err := NewResearchAgent("test-api-key", "http://127.0.0.1:8080")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if agent == nil {
			t.Fatal("expected agent, got nil")
		}
	})

	t.Run("insecure remote http baseURL rejected", func(t *testing.T) {
		agent, err := NewResearchAgent("test-api-key", "http://api.example.com")
		if err == nil {
			t.Fatal("expected error for insecure http baseURL, got nil")
		}
		if agent != nil {
			t.Fatal("expected nil agent on error")
		}
		expectedSubstr := "insecure baseURL"
		if !strings.Contains(err.Error(), expectedSubstr) {
			t.Errorf("error %q does not contain %q", err.Error(), expectedSubstr)
		}
	})

	t.Run("empty baseURL uses default", func(t *testing.T) {
		agent, err := NewResearchAgent("test-api-key", "")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if agent == nil {
			t.Fatal("expected agent, got nil")
		}
	})
}

func TestUploadFilesEmpty(t *testing.T) {
	agent := &ResearchAgent{}
	uris, err := agent.UploadFiles(t.Context(), []string{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(uris) != 0 {
		t.Fatalf("expected empty uris, got %v", uris)
	}
}

func TestUploadFileNonExistent(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	agent := &ResearchAgent{}
	nonExistentPath := filepath.Join("sub", "nonexistent.txt")
	_, err := agent.uploadFile(t.Context(), nonExistentPath)
	if err == nil {
		t.Fatal("expected error for missing file, got nil")
	}
	if !strings.Contains(err.Error(), "file not found") {
		t.Fatalf("error %q does not contain 'file not found'", err.Error())
	}
}

func TestIsSecureOrLoopbackBaseURL(t *testing.T) {
	tests := []struct {
		name string
		url  string
		want bool
	}{
		{name: "https remote", url: "https://api.example.test", want: true},
		{name: "http localhost", url: "http://localhost:8080", want: true},
		{name: "http ipv4 loopback", url: "http://127.0.0.1:8080", want: true},
		{name: "http ipv6 loopback", url: "http://[::1]:8080", want: true},
		{name: "http localhost suffix", url: "http://localhost.evil.test", want: false},
		{name: "http ipv4 prefix", url: "http://127.0.0.1.evil.test", want: false},
		{name: "http remote", url: "http://api.example.test", want: false},
		{name: "unsupported scheme", url: "ftp://localhost", want: false},
		{name: "invalid url", url: "http://[::1", want: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := isSecureOrLoopbackBaseURL(tt.url); got != tt.want {
				t.Fatalf("isSecureOrLoopbackBaseURL(%q) = %v, want %v", tt.url, got, tt.want)
			}
		})
	}
}
