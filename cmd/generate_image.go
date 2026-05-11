package cmd

import (
	"context"
	"fmt"

	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/google/research-cli/internal/utils"
	"github.com/spf13/cobra"
)

var generateImageCmd = &cobra.Command{
	Use:   "generate-image [prompt]",
	Short: "Generate an image from a prompt",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		prompt := args[0]
		outputPath, _ := cmd.Flags().GetString("output")

		apiKey, err := utils.GetApiKey()
		if err != nil {
			return err
		}

		a, err := agent.NewResearchAgent(apiKey, "")
		if err != nil {
			return err
		}

		ctx := context.Background()
		fmt.Printf("Generating image for: %s\n", prompt)

		err = a.GenerateImage(ctx, prompt, outputPath, config.DefaultModel, true)
		if err != nil {
			return err
		}

		ui.PrintSuccess("Image saved to " + utils.SanitizePath(outputPath))
		return nil
	},
}

func init() {
	rootCmd.AddCommand(generateImageCmd)
	generateImageCmd.Flags().StringP("output", "o", "output.png", "Output file path")
}
