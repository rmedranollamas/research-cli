package agent

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/google/research-cli/internal/utils"
	"golang.org/x/sync/errgroup"
	"google.golang.org/genai"
)

func (a *ResearchAgent) UploadFiles(ctx context.Context, filePaths []string) ([]string, error) {
	if len(filePaths) == 0 {
		return nil, nil
	}

	g, ctx := errgroup.WithContext(ctx)
	uris := make([]string, len(filePaths))

	for i, path := range filePaths {
		g.Go(func() error {
			uri, err := a.uploadFile(ctx, path)
			if err != nil {
				return fmt.Errorf("failed to upload %s: %w", path, err)
			}
			uris[i] = uri
			return nil
		})
	}

	if err := g.Wait(); err != nil {
		return nil, err
	}

	result := make([]string, 0, len(uris))
	for _, uri := range uris {
		if uri != "" {
			result = append(result, uri)
		}
	}
	return result, nil
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
	timer := time.NewTimer(0)
	if !timer.Stop() {
		<-timer.C
	}
	defer timer.Stop()

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

		timer.Reset(2 * time.Second)
		select {
		case <-ctx.Done():
			if !timer.Stop() {
				<-timer.C
			}
			return "", ctx.Err()
		case <-timer.C:
		}
	}
}
