package cmd

import (
	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/spf13/cobra"
)

var runCmd = &cobra.Command{
	Use:   "run [query]",
	Short: "Run a deep research task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		return runResearchCommand(cmd, args[0])
	},
}

func runResearchCommand(cmd *cobra.Command, query string) error {
	filePaths, _ := cmd.Flags().GetStringSlice("file")
	urls, _ := cmd.Flags().GetStringSlice("url")
	model, _ := cmd.Flags().GetString("model")
	if !cmd.Flags().Changed("model") {
		model = config.DefaultModel
	}
	parent, _ := cmd.Flags().GetString("parent")
	thinkingLevel, _ := cmd.Flags().GetString("thinking")
	if thinkingLevel == "" {
		thinkingLevel, _ = cmd.Flags().GetString("thinking-level")
	}
	collaborativePlanning, _ := cmd.Flags().GetBool("plan")
	noSearch, _ := cmd.Flags().GetBool("no-search")
	visualization, _ := cmd.Flags().GetBool("visualization")
	visAlias, _ := cmd.Flags().GetBool("vis")
	visualization = visualization || visAlias
	verbose, _ := cmd.Flags().GetBool("verbose")

	a, err := newAgentFromConfig()
	if err != nil {
		return err
	}

	ctx := cmd.Context()
	var fileURIs []string
	if len(filePaths) > 0 {
		fileURIs, err = a.UploadFiles(ctx, filePaths)
		if err != nil {
			return err
		}
	}

	ui.PrintPanel("Deep Research Starting", query, model)

	report, err := a.RunResearch(ctx, query, model, parent, urls, fileURIs, !noSearch, thinkingLevel, collaborativePlanning, visualization, verbose)
	if err != nil {
		return err
	}

	ui.PrintReport(report)

	output, _ := cmd.Flags().GetString("output")
	force, _ := cmd.Flags().GetBool("force")
	return saveReportIfRequested(report, output, force)
}

func init() {
	rootCmd.AddCommand(runCmd)
	runCmd.Flags().StringSlice("file", []string{}, "Local file context (PDF, TXT, Image)")
	runCmd.Flags().StringSliceP("url", "u", []string{}, "URL context")
	runCmd.Flags().StringP("model", "m", config.DefaultModelFallback, "Model ID")
	runCmd.Flags().String("parent", "", "Previous interaction ID")
	runCmd.Flags().String("thinking", "", "Thinking level (minimal, low, medium, high)")
	runCmd.Flags().String("thinking-level", "", "Thinking level")
	runCmd.Flags().Bool("plan", false, "Enable collaborative planning")
	runCmd.Flags().Bool("no-search", false, "Disable Google Search grounding")
	runCmd.Flags().Bool("visualization", false, "Enable automatic visualizations")
	runCmd.Flags().Bool("vis", false, "Enable automatic visualizations")
	runCmd.Flags().BoolP("verbose", "v", false, "Show detailed reasoning thoughts")
	runCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	runCmd.Flags().BoolP("force", "f", false, "Force overwrite output file")
	_ = runCmd.Flags().MarkHidden("thinking-level")
}
