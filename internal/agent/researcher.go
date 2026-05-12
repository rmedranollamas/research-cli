package agent

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/google/research-cli/internal/config"
	"github.com/google/research-cli/internal/db"
	"github.com/google/research-cli/internal/utils"
)

type InteractionRequest struct {
	Agent                 string                 `json:"agent,omitempty"`
	Model                 string                 `json:"model,omitempty"`
	Input                 interface{}            `json:"input"`
	Background            bool                   `json:"background,omitempty"`
	Stream                bool                   `json:"stream,omitempty"`
	AgentConfig           map[string]interface{} `json:"agent_config,omitempty"`
	Tools                 []interface{}          `json:"tools,omitempty"`
	PreviousInteractionID string                 `json:"previous_interaction_id,omitempty"`
	ResponseModalities    []string               `json:"response_modalities,omitempty"`
}

type InteractionResponse struct {
	Interaction struct {
		ID     string `json:"id"`
		Status string `json:"status"`
	} `json:"interaction"`
	Thought struct {
		Text    string `json:"text"`
		Summary string `json:"summary"`
	} `json:"thought"`
	Delta struct {
		Type    string `json:"type"`
		Text    string `json:"text"`
		Content struct {
			Text string `json:"text"`
		} `json:"content"`
	} `json:"delta"`
	Content struct {
		Parts []struct {
			Text string `json:"text"`
		} `json:"parts"`
	} `json:"content"`
}

func (a *ResearchAgent) RunResearch(ctx context.Context, query string, modelID string, parentID string, urls []string, fileURIs []string, useSearch bool, thinkingLevel string, collaborativePlanning bool) (string, error) {
	// Save task to DB
	var pID *string
	if parentID != "" {
		pID = &parentID
	}
	taskID, err := db.SaveTask(query, modelID, nil, pID)
	if err != nil {
		return "", err
	}

	fmt.Printf("Deep Research Starting (Task ID: %d)\n", taskID)

	agentConfig := map[string]interface{}{
		"type":                   "deep-research",
		"thinking_summaries":     "auto",
		"collaborative_planning": collaborativePlanning,
	}
	if thinkingLevel != "" {
		agentConfig["thinking_level"] = thinkingLevel
	}

	content := []map[string]interface{}{
		{"type": "text", "text": query},
	}
	for _, url := range urls {
		content = append(content, map[string]interface{}{
			"type":      "document",
			"uri":       url,
			"mime_type": "text/html",
		})
	}
	for _, uri := range fileURIs {
		content = append(content, map[string]interface{}{
			"type": "document",
			"uri":  uri,
		})
	}

	reqBody := InteractionRequest{
		Agent:       modelID,
		Input:       []interface{}{map[string]interface{}{"role": "user", "content": content}},
		Background:  true,
		Stream:      true,
		AgentConfig: agentConfig,
		Tools:       a.getTools(useSearch, len(urls) > 0),
	}
	if parentID != "" {
		reqBody.PreviousInteractionID = parentID
	}

	return a.streamInteraction(ctx, taskID, reqBody)
}

func (a *ResearchAgent) RunSearch(ctx context.Context, query string, modelID string, parentID string) (string, error) {
	var pID *string
	if parentID != "" {
		pID = &parentID
	}
	taskID, err := db.SaveTask(query, modelID, nil, pID)
	if err != nil {
		return "", err
	}

	fmt.Printf("Fast Search Starting (Task ID: %d)\n", taskID)

	reqBody := InteractionRequest{
		Model:  modelID,
		Input:  query,
		Stream: true,
		Tools:  a.getTools(true, false),
	}
	if parentID != "" {
		reqBody.PreviousInteractionID = parentID
	}

	return a.streamInteraction(ctx, taskID, reqBody)
}

func (a *ResearchAgent) GetStatus(ctx context.Context, interactionID string) (string, error) {
	return a.pollInteraction(ctx, interactionID)
}

func (a *ResearchAgent) GenerateImage(ctx context.Context, prompt string, outputPath string, modelID string, force bool) error {
	reqBody := InteractionRequest{
		Model:              modelID,
		Input:              prompt,
		ResponseModalities: []string{"IMAGE"},
	}

	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return err
	}

	url := a.apiURL("/v1alpha/interactions")
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-goog-api-key", a.apiKey)

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result struct {
		Outputs []struct {
			Type string `json:"type"`
			Data string `json:"data"`
		} `json:"outputs"`
	}
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		return err
	}

	for _, o := range result.Outputs {
		if o.Type == "image" && o.Data != "" {
			decoded, err := base64.StdEncoding.DecodeString(o.Data)
			if err != nil {
				return err
			}
			return utils.SaveToFile(decoded, outputPath, force)
		}
	}

	return fmt.Errorf("no image was generated")
}

func (a *ResearchAgent) getTools(useSearch bool, useURLs bool) []interface{} {
	var tools []interface{}
	if useSearch {
		tools = append(tools, map[string]string{"type": "google_search"})
	}
	if useURLs {
		tools = append(tools, map[string]string{"type": "url_context"})
	}
	tools = append(tools, map[string]string{"type": "code_execution"})

	for i, url := range config.McpServers {
		tools = append(tools, map[string]interface{}{
			"type": "mcp_server",
			"name": fmt.Sprintf("mcp_server_%d", i),
			"url":  url,
		})
	}
	return tools
}

func (a *ResearchAgent) streamInteraction(ctx context.Context, taskID int64, body InteractionRequest) (string, error) {
	jsonBody, err := json.Marshal(body)
	if err != nil {
		return "", err
	}

	url := a.apiURL("/v1alpha/interactions?alt=sse")

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-goog-api-key", a.apiKey)

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	reader := bufio.NewReader(resp.Body)
	var reportParts []string
	var interactionID string
	verbose := os.Getenv("RESEARCH_VERBOSE") == "1"

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				// Handle the last line if it doesn't end with a newline
				if line != "" {
					processSSELine(line, &interactionID, &reportParts, taskID, verbose)
				}
				break
			}
			return "", err
		}

		processSSELine(line, &interactionID, &reportParts, taskID, verbose)
	}

	if !verbose {
		fmt.Println()
	}

	report := strings.Join(reportParts, "")
	if report == "" && interactionID != "" {
		// Fallback to polling
		report, err = a.pollInteraction(ctx, interactionID)
		if err != nil {
			_ = db.UpdateTask(taskID, "FAILED", nil, nil)
			return "", err
		}
	}

	if report != "" {
		_ = db.UpdateTask(taskID, "COMPLETED", &report, &interactionID)
		return report, nil
	}

	_ = db.UpdateTask(taskID, "FAILED", nil, nil)
	return "", fmt.Errorf("no content received")
}

func (a *ResearchAgent) pollInteraction(ctx context.Context, interactionID string) (string, error) {
	fmt.Printf("Polling interaction %s...\n", interactionID)
	interval := 1.0
	maxInterval := config.PollIntervalDefault

	for {
		url := a.apiURL(fmt.Sprintf("/v1alpha/interactions/%s", interactionID))
		req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			return "", err
		}
		req.Header.Set("x-goog-api-key", a.apiKey)

		resp, err := a.httpClient.Do(req)
		if err != nil {
			return "", err
		}

		if resp.StatusCode != http.StatusOK {
			resp.Body.Close()
			if resp.StatusCode >= 500 {
				select {
				case <-ctx.Done():
					return "", ctx.Err()
				case <-time.After(time.Duration(interval) * time.Second):
				}
				interval = min(interval*1.5, maxInterval)
				continue
			}
			return "", fmt.Errorf("polling failed with status %d", resp.StatusCode)
		}

		var result struct {
			Status  string `json:"status"`
			Outputs []struct {
				Text string `json:"text"`
			} `json:"outputs"`
			Response struct {
				Text string `json:"text"`
			} `json:"response"`
			Error string `json:"error"`
		}
		err = json.NewDecoder(resp.Body).Decode(&result)
		resp.Body.Close()
		if err != nil {
			return "", err
		}

		status := strings.ToUpper(result.Status)
		if status == "COMPLETED" {
			var reportParts []string
			for _, o := range result.Outputs {
				if o.Text != "" {
					reportParts = append(reportParts, o.Text)
				}
			}
			if len(reportParts) == 0 && result.Response.Text != "" {
				reportParts = append(reportParts, result.Response.Text)
			}
			return strings.Join(reportParts, ""), nil
		} else if status == "FAILED" || status == "CANCELLED" {
			return "", fmt.Errorf("interaction %s: %s", status, result.Error)
		}

		select {
		case <-ctx.Done():
			return "", ctx.Err()
		case <-time.After(time.Duration(interval) * time.Second):
			interval = min(interval*1.5, maxInterval)
		}
	}
}

func (a *ResearchAgent) apiURL(path string) string {
	base := "https://generativelanguage.googleapis.com"
	if a.baseURL != "" {
		base = strings.TrimSuffix(a.baseURL, "/")
	}
	return base + path
}

func processSSELine(line string, interactionID *string, reportParts *[]string, taskID int64, verbose bool) {
	line = strings.TrimSpace(line)
	if line == "" || !strings.HasPrefix(line, "data: ") {
		return
	}

	data := strings.TrimPrefix(line, "data: ")
	var event InteractionResponse
	if err := json.Unmarshal([]byte(data), &event); err != nil {
		return
	}

	if event.Interaction.ID != "" && *interactionID == "" {
		*interactionID = event.Interaction.ID
		_ = db.UpdateTask(taskID, "IN_PROGRESS", nil, interactionID)
		fmt.Printf("Interaction ID: %s\n", *interactionID)
	}

	thought := event.Thought.Summary
	if thought == "" {
		thought = event.Thought.Text
	}
	if thought != "" {
		if verbose {
			fmt.Printf("> %s\n", thought)
		}
	}

	for _, part := range event.Content.Parts {
		if part.Text != "" {
			*reportParts = append(*reportParts, part.Text)
			if !verbose {
				fmt.Print(part.Text)
			}
		}
	}

	if event.Delta.Type == "text" && event.Delta.Text != "" {
		*reportParts = append(*reportParts, event.Delta.Text)
		if !verbose {
			fmt.Print(event.Delta.Text)
		}
	}
}
