package agent

import (
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/google/research-cli/internal/config"
)

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
	line := `data: {"content":{"parts":[{"text":"hello " }]},"delta":{"type":"text","text":"world"}}`
	var interactionID string
	var reportParts []string

	processSSELine(line, &interactionID, &reportParts, 1, false)

	if got := reportParts; len(got) != 2 || got[0] != "hello " || got[1] != "world" {
		t.Fatalf("reportParts = %#v", got)
	}
}

func TestStreamInteractionReadsSSE(t *testing.T) {
	oldDBPath := config.DbPath
	config.DbPath = filepath.Join(t.TempDir(), "history.db")
	t.Cleanup(func() {
		config.DbPath = oldDBPath
	})

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
