package cmd

import (
	"github.com/google/research-cli/internal/ui"
	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status [interaction_id]",
	Short: "Check the status of a research task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		id := args[0]

		a, err := newAgentFromConfig()
		if err != nil {
			return err
		}

		ctx := cmd.Context()
		report, err := a.GetStatus(ctx, id)
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
	rootCmd.AddCommand(statusCmd)
	statusCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	statusCmd.Flags().BoolP("force", "f", false, "Force overwrite output file")
}
