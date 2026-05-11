package cmd

import (
	"fmt"
	"os"

	"github.com/google/research-cli/internal/config"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "research",
	Short: "A specialized CLI for Gemini Deep Research and multimodal interactions",
	Long: `research-cli is a specialized, stateful CLI for Gemini Deep Research
and multimodal interactions, supporting streaming, polling, and local state management.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		config.Load()
	},
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	// Global flags can be added here
}
