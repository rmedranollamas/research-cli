package utils

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/research-cli/internal/config"
)

func TestSaveToFileRejectsSymlinkOverwrite(t *testing.T) {
	workspace := t.TempDir()
	outside := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	target := filepath.Join(outside, "target.txt")
	if err := os.WriteFile(target, []byte("original"), 0644); err != nil {
		t.Fatal(err)
	}

	link := filepath.Join(workspace, "output.txt")
	if err := os.Symlink(target, link); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}

	err := SaveToFile([]byte("new"), link, true)
	if err == nil {
		t.Fatal("SaveToFile succeeded; want symlink overwrite rejection")
	}

	data, err := os.ReadFile(target)
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != "original" {
		t.Fatalf("target was overwritten: got %q", data)
	}
}

func TestSaveToFileRejectsExistingFileWithoutForce(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	path := filepath.Join(workspace, "output.txt")
	if err := os.WriteFile(path, []byte("original"), 0644); err != nil {
		t.Fatal(err)
	}

	err := SaveToFile([]byte("new"), path, false)
	if err == nil || !strings.Contains(err.Error(), "already exists") {
		t.Fatalf("SaveToFile error = %v, want already exists", err)
	}
}

func TestValidatePathAllowsDotDotPrefixedNamesInsideWorkspace(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	want := filepath.Join(workspace, "..cache", "out.txt")
	got, err := ValidatePath(filepath.Join(".", "..cache", "out.txt"))
	if err != nil {
		t.Fatalf("ValidatePath returned error for valid workspace path: %v", err)
	}
	if got != want {
		t.Fatalf("ValidatePath() = %q, want %q", got, want)
	}
}

func TestValidatePathRejectsParentTraversal(t *testing.T) {
	workspace := t.TempDir()
	oldWorkspace := config.WorkspaceDir
	config.WorkspaceDir = workspace
	t.Cleanup(func() {
		config.WorkspaceDir = oldWorkspace
	})

	if _, err := ValidatePath(filepath.Join("..", "outside.txt")); err == nil {
		t.Fatal("ValidatePath accepted parent traversal")
	}
}
