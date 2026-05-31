package cmd

import (
	"testing"
	"unicode/utf8"
)

func TestTruncateRunesPreservesUTF8(t *testing.T) {
	input := "研究研究研究研究研究研究研究研究研究研究研究研究研究研究研究研究研究研究"
	got := truncateRunes(input, 10)
	want := "研究研究研究研..."

	if got != want {
		t.Fatalf("truncateRunes() = %q, want %q", got, want)
	}
	if !utf8.ValidString(got) {
		t.Fatalf("truncateRunes() returned invalid UTF-8: %q", got)
	}
}

func TestTruncateRunesEdgeCases(t *testing.T) {
	tests := []struct {
		input string
		limit int
		want  string
	}{
		{"abc", 3, "abc"},
		{"abc", 2, "ab"},
		{"abc", 4, "abc"},
		{"abcd", 3, "abc"},
		{"abcde", 4, "a..."},
		{"abcde", 5, "abcde"},
		{"", 5, ""},
		{"abc", 0, ""},
		{"研究研究", 2, "研究"},
		{"研究研究", 3, "研究研"},
		{"研究研究", 4, "研究研究"},
		{"研究研究研究", 5, "研究..."},
	}

	for _, tt := range tests {
		got := truncateRunes(tt.input, tt.limit)
		if got != tt.want {
			t.Errorf("truncateRunes(%q, %d) = %q, want %q", tt.input, tt.limit, got, tt.want)
		}
	}
}
