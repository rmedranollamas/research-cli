package cmd

import (
	"github.com/google/research-cli/internal/agent"
	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/ui"
	"github.com/google/research-cli/internal/utils"
)

func newAgentFromConfig() (*agent.ResearchAgent, error) {
	apiKey, err := utils.GetApiKey()
	if err != nil {
		return nil, err
	}
	return agent.NewResearchAgent(apiKey, config.GeminiApiBaseUrl)
}

func saveReportIfRequested(report, output string, force bool) error {
	if output == "" || report == "" {
		return nil
	}
	if err := utils.SaveToFile([]byte(report), output, force); err != nil {
		return err
	}
	ui.PrintPanel("Success", "Report saved to "+utils.SanitizePath(output), "")
	return nil
}
