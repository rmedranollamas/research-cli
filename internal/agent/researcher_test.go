package agent

import (
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/db"
)

func resetDBForAgentTest(t *testing.T) {
	t.Helper()
	db.ResetDBForTesting()
	oldDBPath := config.DbPath
	config.DbPath = filepath.Join(t.TempDir(), "history.db")
	t.Cleanup(func() {
		db.ResetDBForTesting()
		config.DbPath = oldDBPath
	})
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req)
}

func TestAPIURLUsesCustomBaseURL(t *testing.T) {
	a := &ResearchAgent{baseURL: "https://proxy.example.test/root/"}

	got := a.apiURL("/v1alpha/interactions/abc")
	want := "https://proxy.example.test/root/v1alpha/interactions/abc"

	if got != want {
		t.Fatalf("apiURL() = %q, want %q", got, want)
	}
}

func TestAPIURLUsesDefaultBaseURL(t *testing.T) {
	a := &ResearchAgent{}

	got := a.apiURL("/v1alpha/interactions?alt=sse")
	want := "https://generativelanguage.googleapis.com/v1alpha/interactions?alt=sse"

	if got != want {
		t.Fatalf("apiURL() = %q, want %q", got, want)
	}
}

func TestBackoffDurationPreservesFractionalSeconds(t *testing.T) {
	got := backoffDuration(1.5)
	want := 1500 * time.Millisecond

	if got != want {
		t.Fatalf("backoffDuration() = %s, want %s", got, want)
	}
}

func TestSanitizeTerminalTextRemovesControlCharacters(t *testing.T) {
	got := sanitizeTerminalText("ok\x1b[31m red\x1b[0m\x00\nnext\t")
	want := "ok red\nnext\t"

	if got != want {
		t.Fatalf("sanitizeTerminalText() = %q, want %q", got, want)
	}
}

func TestSanitizeTerminalTextRemovesANSIControlSequences(t *testing.T) {
	got := sanitizeTerminalText("\x1b]0;title\ahello\x1b[2Jworld")
	want := "helloworld"

	if got != want {
		t.Fatalf("sanitizeTerminalText() = %q, want %q", got, want)
	}
}

func TestGetToolsIncludesRequestedToolsAndMCPServers(t *testing.T) {
	oldServers := config.McpServers
	config.McpServers = []string{"https://mcp.example.test"}
	t.Cleanup(func() {
		config.McpServers = oldServers
	})

	a := &ResearchAgent{}
	tools := a.getTools(true, true)

	if len(tools) != 4 {
		t.Fatalf("len(tools) = %d, want 4: %#v", len(tools), tools)
	}
}

func TestProcessSSELineAppendsContentAndDelta(t *testing.T) {
	resetDBForAgentTest(t)
	line := `data: {"content":{"parts":[{"text":"hello " }]},"delta":{"type":"text","text":"world"}}`
	var interactionID string
	var reportParts []string

	processSSELine(line, &interactionID, &reportParts, 1, false)

	if got := reportParts; len(got) != 2 || got[0] != "hello " || got[1] != "world" {
		t.Fatalf("reportParts = %#v", got)
	}
}

func TestProcessSSELineImageDelta(t *testing.T) {
	resetDBForAgentTest(t)
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	pngBytes := []byte{0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a}
	encoded := base64.StdEncoding.EncodeToString(pngBytes)
	line := fmt.Sprintf(`data: {"delta":{"type":"image","data":"%s"}}`, encoded)

	var interactionID string
	var reportParts []string

	processSSELine(line, &interactionID, &reportParts, 123, true)

	files, err := os.ReadDir(workspace)
	if err != nil {
		t.Fatal(err)
	}
	if len(files) == 0 {
		t.Fatal("expected image file to be saved, found none")
	}
	if !strings.HasPrefix(files[0].Name(), "research_task_123_") {
		t.Fatalf("unexpected filename: %s", files[0].Name())
	}
}

func TestProcessSSELineInvalidJSON(t *testing.T) {
	resetDBForAgentTest(t)
	line := `data: {invalid json`
	var interactionID string
	var reportParts []string
	processSSELine(line, &interactionID, &reportParts, 1, false)
	if len(reportParts) != 0 {
		t.Fatalf("expected 0 report parts for invalid json, got %d", len(reportParts))
	}
}

func TestStreamInteractionReadsSSE(t *testing.T) {
	resetDBForAgentTest(t)

	client := &http.Client{
		Transport: roundTripFunc(func(req *http.Request) (*http.Response, error) {
			if req.URL.String() != "https://proxy.example.test/v1alpha/interactions?alt=sse" {
				t.Fatalf("unexpected request URL: %s", req.URL.String())
			}
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(strings.NewReader("data: {\"interaction\":{\"id\":\"abc\"},\"delta\":{\"type\":\"text\",\"text\":\"done\"}}\n")),
				Header:     make(http.Header),
				Request:    req,
			}, nil
		}),
	}

	a := &ResearchAgent{
		apiKey:     "test-key",
		baseURL:    "https://proxy.example.test",
		httpClient: client,
	}

	report, err := a.streamInteraction(t.Context(), 123, InteractionRequest{Input: "query"}, false)
	if err != nil {
		t.Fatal(err)
	}
	if report != "done" {
		t.Fatalf("report = %q, want done", report)
	}
}

func TestStreamInteractionHTTPError(t *testing.T) {
	resetDBForAgentTest(t)

	client := &http.Client{
		Transport: roundTripFunc(func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusBadRequest,
				Body:       io.NopCloser(strings.NewReader("bad request")),
				Header:     make(http.Header),
				Request:    req,
			}, nil
		}),
	}

	a := &ResearchAgent{
		apiKey:     "test-key",
		baseURL:    "https://proxy.example.test",
		httpClient: client,
	}

	_, err := a.streamInteraction(t.Context(), 123, InteractionRequest{Input: "query"}, false)
	if err == nil {
		t.Fatal("expected error, got nil")
	}
	if !strings.Contains(err.Error(), "status 400") {
		t.Fatalf("unexpected error message: %v", err)
	}
}

func TestRunResearchAndRunSearch(t *testing.T) {
	resetDBForAgentTest(t)

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("data: {\"interaction\":{\"id\":\"inter-123\"},\"delta\":{\"type\":\"text\",\"text\":\"result report\"}}\n"))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	t.Run("RunResearch success", func(t *testing.T) {
		report, err := a.RunResearch(t.Context(), "research query", "model-1", "parent-1", []string{"https://example.com"}, []string{"file://uri1"}, true, "high", true, true, false)
		if err != nil {
			t.Fatalf("RunResearch error: %v", err)
		}
		if report != "result report" {
			t.Fatalf("report = %q, want 'result report'", report)
		}
	})

	t.Run("RunSearch success", func(t *testing.T) {
		report, err := a.RunSearch(t.Context(), "search query", "model-2", "", false)
		if err != nil {
			t.Fatalf("RunSearch error: %v", err)
		}
		if report != "result report" {
			t.Fatalf("report = %q, want 'result report'", report)
		}
	})
}

func TestPollInteractionSuccess(t *testing.T) {
	resetDBForAgentTest(t)

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"COMPLETED","outputs":[{"text":"polled output"}]}`))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	report, err := a.GetStatus(t.Context(), "inter-999")
	if err != nil {
		t.Fatalf("GetStatus error: %v", err)
	}
	if report != "polled output" {
		t.Fatalf("report = %q, want 'polled output'", report)
	}
}

func TestPollInteractionFailed(t *testing.T) {
	resetDBForAgentTest(t)

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"FAILED","error":"task execution error"}`))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	_, err = a.GetStatus(t.Context(), "inter-failed")
	if err == nil {
		t.Fatal("expected error, got nil")
	}
	if !strings.Contains(err.Error(), "FAILED: task execution error") {
		t.Fatalf("unexpected error message: %v", err)
	}
}

func TestGenerateImageSuccess(t *testing.T) {
	resetDBForAgentTest(t)
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	imgData := []byte("fake-image-bytes")
	b64Data := base64.StdEncoding.EncodeToString(imgData)

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(fmt.Sprintf(`{"outputs":[{"type":"image","data":"%s"}]}`, b64Data)))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	outPath := filepath.Join(workspace, "gen.png")
	err = a.GenerateImage(t.Context(), "draw a cat", outPath, "model-img", true)
	if err != nil {
		t.Fatalf("GenerateImage error: %v", err)
	}

	got, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != string(imgData) {
		t.Fatalf("saved image content = %q, want %q", string(got), string(imgData))
	}
}

func TestGenerateImageNoOutput(t *testing.T) {
	resetDBForAgentTest(t)

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"outputs":[]}`))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	err = a.GenerateImage(t.Context(), "prompt", "out.png", "model-img", true)
	if err == nil {
		t.Fatal("expected error when no image output, got nil")
	}
	if !strings.Contains(err.Error(), "no image was generated") {
		t.Fatalf("unexpected error message: %v", err)
	}
}

func TestStreamInteractionFallbackPolling(t *testing.T) {
	resetDBForAgentTest(t)

	// Pre-create task in DB
	taskID, err := db.SaveTask("query", "model", nil, nil)
	if err != nil {
		t.Fatal(err)
	}

	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "interactions/poll-id") {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"COMPLETED","response":{"text":"polled fallback text"}}`))
			return
		}
		// SSE stream returns interaction ID without report parts
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("data: {\"interaction\":{\"id\":\"poll-id\"}}\n"))
	}))
	t.Cleanup(ts.Close)

	a, err := NewResearchAgent("test-api-key", ts.URL)
	if err != nil {
		t.Fatal(err)
	}

	report, err := a.streamInteraction(t.Context(), taskID, InteractionRequest{Input: "query"}, false)
	if err != nil {
		t.Fatalf("streamInteraction fallback error: %v", err)
	}
	if report != "polled fallback text" {
		t.Fatalf("report = %q, want 'polled fallback text'", report)
	}
}
