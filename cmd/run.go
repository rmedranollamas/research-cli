package cmd

import (
	"context"
	"os"

	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/google/research-cli/internal/utils"
	"github.com/spf13/cobra"
)

var runCmd = &cobra.Command{
	Use:   "run [query]",
	Short: "Run a deep research task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		query := args[0]
		filePaths, _ := cmd.Flags().GetStringSlice("file")
		urls, _ := cmd.Flags().GetStringSlice("url")
		
		apiKey, err := utils.GetApiKey()
		if err != nil {
			return err
		}

		a, err := agent.NewResearchAgent(apiKey, config.GeminiApiBaseUrl)
		if err != nil {
			return err
		}

		ctx := context.Background()
		var fileURIs []string
		if len(filePaths) > 0 {
			fileURIs, err = a.UploadFiles(ctx, filePaths)
			if err != nil {
				return err
			}
		}

		ui.PrintPanel("Deep Research Starting", query, config.DefaultModel)
		
		thinkingLevel, _ := cmd.Flags().GetString("thinking-level")
		collaborativePlanning, _ := cmd.Flags().GetBool("plan")
		noSearch, _ := cmd.Flags().GetBool("no-search")
		verbose, _ := cmd.Flags().GetBool("verbose")

		if verbose {
			os.Setenv("RESEARCH_VERBOSE", "1")
		}

		report, err := a.RunResearch(ctx, query, config.DefaultModel, "", urls, fileURIs, !noSearch, thinkingLevel, collaborativePlanning)
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
	rootCmd.AddCommand(runCmd)
	runCmd.Flags().StringSliceP("file", "f", []string{}, "Local file context (PDF, TXT, Image)")
	runCmd.Flags().StringSliceP("url", "u", []string{}, "URL context")
	runCmd.Flags().String("thinking-level", "auto", "Thinking level (auto, basic, medium, deep)")
	runCmd.Flags().Bool("plan", false, "Enable collaborative planning")
	runCmd.Flags().Bool("no-search", false, "Disable Google Search grounding")
	runCmd.Flags().BoolP("verbose", "v", false, "Show detailed reasoning thoughts")
	runCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	runCmd.Flags().Bool("force", false, "Force overwrite output file")
}
