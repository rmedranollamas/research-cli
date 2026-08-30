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
	tests := []struct {
		name             string
		msg              string
		expectedContains []string
	}{
		{
			name:             "standard error message",
			msg:              "test error",
			expectedContains: []string{"Error: test error"},
		},
		{
			name:             "empty message",
			msg:              "",
			expectedContains: []string{"Error: "},
		},
		{
			name:             "special characters",
			msg:              "failed with status 500: @#$%^&*()",
			expectedContains: []string{"Error: failed with status 500: @#$%^&*()"},
		},
		{
			name:             "multiline error message",
			msg:              "first line\nsecond line",
			expectedContains: []string{"Error: first line", "second line"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := captureOutput(func() {
				PrintError(tt.msg)
			})
			gotClean := stripANSI(got)
			for _, exp := range tt.expectedContains {
				if !strings.Contains(gotClean, exp) {
					t.Errorf("PrintError(%q) output missing %q, got: %q", tt.msg, exp, gotClean)
				}
			}
		})
	}
}

func TestPrintSuccess(t *testing.T) {
	tests := []struct {
		name             string
		msg              string
		expectedContains []string
	}{
		{
			name:             "standard success message",
			msg:              "test success",
			expectedContains: []string{"test success"},
		},
		{
			name:             "empty message",
			msg:              "",
			expectedContains: []string{""},
		},
		{
			name:             "special characters",
			msg:              "Task #123 completed successfully!",
			expectedContains: []string{"Task #123 completed successfully!"},
		},
		{
			name:             "multiline success message",
			msg:              "step 1 complete\nstep 2 complete",
			expectedContains: []string{"step 1 complete", "step 2 complete"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := captureOutput(func() {
				PrintSuccess(tt.msg)
			})
			gotClean := stripANSI(got)
			for _, exp := range tt.expectedContains {
				if !strings.Contains(gotClean, exp) {
					t.Errorf("PrintSuccess(%q) output missing %q, got: %q", tt.msg, exp, gotClean)
				}
			}
		})
	}
}

func TestPrintReport(t *testing.T) {
	tests := []struct {
		name             string
		report           string
		expectedContains []string
	}{
		{
			name:             "standard markdown report",
			report:           "# Research Report\n\n- Finding 1\n- Finding 2",
			expectedContains: []string{"Research Report", "Finding 1", "Finding 2"},
		},
		{
			name:             "empty report",
			report:           "",
			expectedContains: []string{},
		},
		{
			name:             "report with code block",
			report:           "```go\nfunc main() {}\n```",
			expectedContains: []string{"main"},
		},
	}

	separator := strings.Repeat("=", 40)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := captureOutput(func() {
				PrintReport(tt.report)
			})

			// Verify header and footer separators exist
			if strings.Count(got, separator) != 2 {
				t.Errorf("PrintReport() output expected 2 separator lines, got count %d in output: %q", strings.Count(got, separator), got)
			}

			// Verify expected content sub-strings exist
			for _, exp := range tt.expectedContains {
				if !strings.Contains(got, exp) {
					t.Errorf("PrintReport() output missing expected string %q", exp)
				}
			}
		})
	}
}

func TestPrintPanel(t *testing.T) {
	tests := []struct {
		name             string
		title            string
		query            string
		model            string
		expectedContains []string
	}{
		{
			name:  "standard panel",
			title: "test title",
			query: "test query",
			model: "test model",
			expectedContains: []string{
				"=== test title ===",
				"Query: test query",
				"Model: test model",
			},
		},
		{
			name:  "empty fields",
			title: "",
			query: "",
			model: "",
			expectedContains: []string{
				"===  ===",
				"Query: ",
				"Model: ",
			},
		},
		{
			name:  "special characters in panel",
			title: "Research & Analysis",
			query: "What is 1 + 1? (math)",
			model: "gemini-3-flash-preview",
			expectedContains: []string{
				"=== Research & Analysis ===",
				"Query: What is 1 + 1? (math)",
				"Model: gemini-3-flash-preview",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := captureOutput(func() {
				PrintPanel(tt.title, tt.query, tt.model)
			})
			gotClean := stripANSI(got)
			for _, exp := range tt.expectedContains {
				if !strings.Contains(gotClean, exp) {
					t.Errorf("PrintPanel() output missing %q, got: %q", exp, gotClean)
				}
			}
		})
	}
}
