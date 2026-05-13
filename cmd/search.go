package cmd

import (
	"context"

	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/config"
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

		a, err := agent.NewResearchAgent(apiKey, config.GeminiApiBaseUrl)
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

		output, _ := cmd.Flags().GetString("output")
		force, _ := cmd.Flags().GetBool("force")
		if output != "" && report != "" {
			if err := utils.SaveToFile([]byte(report), output, force); err != nil {
				return err
			}
			ui.PrintPanel("Success", "Report saved to "+utils.SanitizePath(output), "")
		}
		return nil
	},
}

func init() {
	rootCmd.AddCommand(searchCmd)
	searchCmd.Flags().StringP("model", "m", "gemini-2.0-flash", "Model to use for fast search")
	searchCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	searchCmd.Flags().Bool("force", false, "Force overwrite output file")
}
