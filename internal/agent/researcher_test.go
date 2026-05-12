package agent

import "testing"

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
