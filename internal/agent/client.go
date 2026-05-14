package agent

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/url"
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
		if !isSecureOrLoopbackBaseURL(baseURL) {
			return nil, fmt.Errorf("insecure baseURL: custom baseURL must use HTTPS to prevent API key exposure")
		}
	}

	clientConfig := &genai.ClientConfig{
		APIKey: apiKey,
		HTTPOptions: genai.HTTPOptions{
			APIVersion: "v1alpha",
		},
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

func isSecureOrLoopbackBaseURL(rawURL string) bool {
	parsed, err := url.Parse(rawURL)
	if err != nil {
		return false
	}
	if parsed.Scheme == "https" {
		return true
	}
	if parsed.Scheme != "http" {
		return false
	}

	host := parsed.Hostname()
	if strings.EqualFold(host, "localhost") {
		return true
	}
	ip := net.ParseIP(host)
	return ip != nil && ip.IsLoopback()
}
