package ui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss"
)

var (
	errorStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("9"))
	successStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("10"))
	headerStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("12")).Bold(true)
)

func PrintError(msg string) {
	fmt.Println(errorStyle.Render("Error: " + msg))
}

func PrintSuccess(msg string) {
	fmt.Println(successStyle.Render(msg))
}

func PrintReport(report string) {
	r, _ := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(100),
	)

	out, _ := r.Render(report)
	fmt.Println("\n" + strings.Repeat("=", 40) + "\n")
	fmt.Print(out)
	fmt.Println("\n" + strings.Repeat("=", 40) + "\n")
}

func PrintPanel(title string, query string, model string) {
	fmt.Println(headerStyle.Render("\n=== " + title + " ==="))
	fmt.Printf("Query: %s\n", query)
	fmt.Printf("Model: %s\n\n", model)
}
