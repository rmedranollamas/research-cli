package cmd

import (
	"fmt"

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
		model, _ := cmd.Flags().GetString("model")
		force, _ := cmd.Flags().GetBool("force")

		a, err := newAgentFromConfig()
		if err != nil {
			return err
		}

		ctx := cmd.Context()
		fmt.Printf("Generating image for: %s\n", prompt)

		err = a.GenerateImage(ctx, prompt, outputPath, model, force)
		if err != nil {
			return err
		}

		ui.PrintSuccess("Image saved to " + utils.SanitizePath(outputPath))
		return nil
	},
}

func init() {
	rootCmd.AddCommand(generateImageCmd)
	generateImageCmd.Flags().StringP("output", "o", "generated_image.png", "Output file path")
	generateImageCmd.Flags().BoolP("force", "f", false, "Force overwrite output file")
	generateImageCmd.Flags().String("model", "gemini-3-pro-image-preview", "Model ID")
}
