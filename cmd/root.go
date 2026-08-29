package cmd

import (
	"fmt"
	"os"

	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/spf13/cobra"
)

var version = "0.3.2"

var rootCmd = &cobra.Command{
	Use:   "research",
	Short: "A specialized CLI for Gemini Deep Research and multimodal interactions",
	Long: `research-cli is a specialized, stateful CLI for Gemini Deep Research
and multimodal interactions, supporting streaming, polling, and local state management.`,
	Args: cobra.ArbitraryArgs,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		config.Load()
	},
	RunE: func(cmd *cobra.Command, args []string) error {
		version, _ := cmd.Flags().GetBool("version")
		if version {
			fmt.Printf("research-cli %s\n", getVersionString())
			return nil
		}
		if len(args) > 0 {
			return runDefaultQuery(cmd, args[0])
		}
		return cmd.Help()
	},
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	rootCmd.Flags().Bool("version", false, "Print the version number")
}

func runDefaultQuery(cmd *cobra.Command, query string) error {
	a, err := newAgentFromConfig()
	if err != nil {
		return err
	}

	ui.PrintPanel("Deep Research Starting", query, config.DefaultModel)
	report, err := a.RunResearch(cmd.Context(), query, config.DefaultModel, "", nil, nil, true, "", false, false, false)
	if err != nil {
		return err
	}

	ui.PrintReport(report)
	return nil
}

func getVersionString() string {
	if version == "" {
		return "unknown"
	}
	return version
}
