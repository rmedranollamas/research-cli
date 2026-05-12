package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/research-cli/internal/config"
)

// ValidatePath ensures the path is within the WorkspaceDir.
func ValidatePath(path string) (string, error) {
	if path == "" {
		return "", fmt.Errorf("empty or invalid path provided")
	}

	absWorkspace, err := filepath.Abs(config.WorkspaceDir)
	if err != nil {
		return "", err
	}
	absWorkspace = filepath.Clean(absWorkspace)

	var absPath string
	if !filepath.IsAbs(path) {
		absPath = filepath.Join(absWorkspace, path)
	} else {
		absPath = path
	}

	absPath, err = filepath.Abs(absPath)
	if err != nil {
		return "", err
	}
	absPath = filepath.Clean(absPath)

	// In Go, we can use strings.HasPrefix on Cleaned absolute paths
	// after ensuring the workspace path has a trailing separator to avoid partial matches
	// e.g., /home/pi/work and /home/pi/workspace
	rel, err := filepath.Rel(absWorkspace, absPath)
	if err != nil {
		return "", fmt.Errorf("path traversal detected: %s is outside the workspace", path)
	}

	if strings.HasPrefix(rel, "..") {
		return "", fmt.Errorf("path traversal detected: %s is outside the workspace", path)
	}

	return absPath, nil
}

// SanitizePath makes a path relative to WorkspaceDir if possible.
func SanitizePath(path string) string {
	if path == "" {
		return ""
	}

	absWorkspace, err := filepath.Abs(config.WorkspaceDir)
	if err != nil {
		return filepath.Base(path)
	}

	absPath, err := filepath.Abs(path)
	if err != nil {
		return filepath.Base(path)
	}

	rel, err := filepath.Rel(absWorkspace, absPath)
	if err != nil || strings.HasPrefix(rel, "..") {
		return filepath.Base(path)
	}

	return rel
}

// SaveToFile securely saves data to a file.
func SaveToFile(data []byte, outputPath string, force bool) error {
	validatedPath, err := ValidatePath(outputPath)
	if err != nil {
		return err
	}

	f, err := openOutputFile(validatedPath, force)
	if err != nil {
		if os.IsExist(err) {
			return fmt.Errorf("output file %s already exists. Use --force to overwrite", SanitizePath(validatedPath))
		}
		return err
	}
	defer f.Close()

	_, err = f.Write(data)
	return err
}

func GetApiKey() (string, error) {
	apiKey := os.Getenv(config.GeminiApiKeyVar)
	if apiKey == "" {
		return "", fmt.Errorf("%s environment variable not set", config.GeminiApiKeyVar)
	}
	return apiKey, nil
}
