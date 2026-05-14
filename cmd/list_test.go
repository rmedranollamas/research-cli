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
