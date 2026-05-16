package cmd

import (
	"github.com/google/research-cli/internal/ui"
	"github.com/spf13/cobra"
)

var searchCmd = &cobra.Command{
	Use:   "search [query]",
	Short: "Run a fast search task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		query := args[0]
		model, _ := cmd.Flags().GetString("model")
		parent, _ := cmd.Flags().GetString("parent")
		verbose, _ := cmd.Flags().GetBool("verbose")

		a, err := newAgentFromConfig()
		if err != nil {
			return err
		}

		ctx := cmd.Context()
		ui.PrintPanel("Fast Search Starting", query, model)

		report, err := a.RunSearch(ctx, query, model, parent, verbose)
		if err != nil {
			return err
		}

		ui.PrintReport(report)

		output, _ := cmd.Flags().GetString("output")
		force, _ := cmd.Flags().GetBool("force")
		return saveReportIfRequested(report, output, force)
	},
}

func init() {
	rootCmd.AddCommand(searchCmd)
	searchCmd.Flags().StringP("model", "m", "gemini-3-flash-preview", "Model to use for fast search")
	searchCmd.Flags().String("parent", "", "Previous interaction ID")
	searchCmd.Flags().BoolP("verbose", "v", false, "Show detailed reasoning thoughts")
	searchCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	searchCmd.Flags().BoolP("force", "f", false, "Force overwrite output file")
}
