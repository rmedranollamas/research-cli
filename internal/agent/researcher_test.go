package agent

import (
	"testing"
	"time"
)

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
	got := sanitizeTerminalText("ok\x1b[31m red\x00\nnext\t")
	want := "ok[31m red\nnext\t"

	if got != want {
		t.Fatalf("sanitizeTerminalText() = %q, want %q", got, want)
	}
}
