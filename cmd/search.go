package cmd

import (
	"context"

	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/ui"
	"github.com/google/research-cli/internal/utils"
	"github.com/spf13/cobra"
)

var searchCmd = &cobra.Command{
	Use:   "search [query]",
	Short: "Run a fast search task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		query := args[0]
		model, _ := cmd.Flags().GetString("model")

		apiKey, err := utils.GetApiKey()
		if err != nil {
			return err
		}

		a, err := agent.NewResearchAgent(apiKey, "")
		if err != nil {
			return err
		}

		ctx := context.Background()
		ui.PrintPanel("Fast Search Starting", query, model)

		report, err := a.RunSearch(ctx, query, model, "")
		if err != nil {
			return err
		}

		ui.PrintReport(report)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(searchCmd)
	searchCmd.Flags().StringP("model", "m", "gemini-2.0-flash", "Model to use for fast search")
}
