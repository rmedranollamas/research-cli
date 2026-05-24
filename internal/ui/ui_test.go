package ui

import (
	"bytes"
	"io"
	"os"
	"regexp"
	"strings"
	"testing"
)

var ansiEscapeRE = regexp.MustCompile(`\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])`)

func stripANSI(s string) string {
	return ansiEscapeRE.ReplaceAllString(s, "")
}

func captureOutput(f func()) string {
	old := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	defer func() {
		os.Stdout = old
	}()

	outC := make(chan string)
	// copy the output in a separate goroutine so printing can't block
	go func() {
		var buf bytes.Buffer
		io.Copy(&buf, r)
		outC <- buf.String()
	}()

	f()
	w.Close()
	return <-outC
}

func TestPrintError(t *testing.T) {
	got := captureOutput(func() {
		PrintError("test error")
	})
	got = stripANSI(got)
	want := "Error: test error\n"
	if got != want {
		t.Errorf("PrintError() = %q, want %q", got, want)
	}
}

func TestPrintSuccess(t *testing.T) {
	got := captureOutput(func() {
		PrintSuccess("test success")
	})
	got = stripANSI(got)
	want := "test success\n"
	if got != want {
		t.Errorf("PrintSuccess() = %q, want %q", got, want)
	}
}

func TestPrintReport(t *testing.T) {
	report := "test report content"
	got := captureOutput(func() {
		PrintReport(report)
	})
	// PrintReport uses glamour which might add its own styling/newlines
	// We check for the separators and the content
	separator := strings.Repeat("=", 40)
	if !strings.Contains(got, separator) {
		t.Errorf("PrintReport() output missing separator")
	}
	if !strings.Contains(got, "test report content") {
		t.Errorf("PrintReport() output missing content")
	}
}

func TestPrintPanel(t *testing.T) {
	got := captureOutput(func() {
		PrintPanel("test title", "test query", "test model")
	})
	got = stripANSI(got)
	if !strings.Contains(got, "=== test title ===") {
		t.Errorf("PrintPanel() output missing title")
	}
	if !strings.Contains(got, "Query: test query") {
		t.Errorf("PrintPanel() output missing query")
	}
	if !strings.Contains(got, "Model: test model") {
		t.Errorf("PrintPanel() output missing model")
	}
}
