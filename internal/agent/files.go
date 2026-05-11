package agent

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/google/research-cli/internal/utils"
	"google.golang.org/genai"
)

func (a *ResearchAgent) UploadFiles(ctx context.Context, filePaths []string) ([]string, error) {
	var uris []string
	for _, path := range filePaths {
		uri, err := a.uploadFile(ctx, path)
		if err != nil {
			fmt.Printf("Error uploading %s: %v\n", path, err)
			continue
		}
		if uri != "" {
			uris = append(uris, uri)
		}
	}
	return uris, nil
}

func (a *ResearchAgent) uploadFile(ctx context.Context, path string) (string, error) {
	validatedPath, err := utils.ValidatePath(path)
	if err != nil {
		return "", err
	}

	if _, err := os.Stat(validatedPath); os.IsNotExist(err) {
		return "", fmt.Errorf("file not found: %s", path)
	}

	filename := filepath.Base(validatedPath)
	fmt.Printf("Uploading %s...\n", filename)

	file, err := a.client.Files.UploadFromPath(ctx, validatedPath, nil)
	if err != nil {
		return "", fmt.Errorf("failed to upload %s: %w", filename, err)
	}

	fmt.Printf("Processing %s...\n", filename)
	for {
		f, err := a.client.Files.Get(ctx, file.Name, nil)
		if err != nil {
			return "", fmt.Errorf("failed to get file status: %w", err)
		}

		if f.State == genai.FileStateActive {
			fmt.Printf("Uploaded %s\n", filename)
			return f.URI, nil
		} else if f.State == genai.FileStateFailed {
			return "", fmt.Errorf("file processing failed with state: %v", f.State)
		}

		select {
		case <-ctx.Done():
			return "", ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
}
