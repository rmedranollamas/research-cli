package agent

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"google.golang.org/genai"
)

type ResearchAgent struct {
	client     *genai.Client
	apiKey     string
	baseURL    string
	httpClient *http.Client
}

func NewResearchAgent(apiKey string, baseURL string) (*ResearchAgent, error) {
	ctx := context.Background()

	httpClient := &http.Client{
		Timeout: 300 * time.Second, // Long timeout for research
	}

	if baseURL != "" {
		isLocal := strings.Contains(baseURL, "localhost") || strings.Contains(baseURL, "127.0.0.1")
		if !strings.HasPrefix(baseURL, "https://") && !isLocal {
			return nil, fmt.Errorf("insecure baseURL: custom baseURL must use HTTPS to prevent API key exposure")
		}
	}

	clientConfig := &genai.ClientConfig{
		APIKey: apiKey,
	}
	if baseURL != "" {
		clientConfig.HTTPOptions.BaseURL = strings.TrimSuffix(baseURL, "/")
	}

	client, err := genai.NewClient(ctx, clientConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create Gemini client: %w", err)
	}

	return &ResearchAgent{
		client:     client,
		apiKey:     apiKey,
		baseURL:    baseURL,
		httpClient: httpClient,
	}, nil
}

func (a *ResearchAgent) GetClient() *genai.Client {
	return a.client
}
