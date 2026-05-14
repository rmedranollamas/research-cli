package cmd

import (
	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/google/research-cli/internal/utils"
	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status [interaction_id]",
	Short: "Check the status of a research task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		id := args[0]

		apiKey, err := utils.GetApiKey()
		if err != nil {
			return err
		}

		a, err := agent.NewResearchAgent(apiKey, config.GeminiApiBaseUrl)
		if err != nil {
			return err
		}

		ctx := cmd.Context()
		report, err := a.GetStatus(ctx, id)
		if err != nil {
			return err
		}

		ui.PrintReport(report)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(statusCmd)
}
