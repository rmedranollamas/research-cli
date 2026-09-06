package db

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/research-cli/internal/config"
)

func resetTestDB(t *testing.T, path string) {
	t.Helper()
	ResetDBForTesting()
	oldPath := config.DbPath
	config.DbPath = path
	t.Cleanup(func() {
		ResetDBForTesting()
		config.DbPath = oldPath
	})
}

func TestTaskLifecycle(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "history.db")
	resetTestDB(t, dbPath)

	parentID := "parent-1"
	interactionIDInit := "interaction-init"
	taskID, err := SaveTask("query", "model", &interactionIDInit, &parentID)
	if err != nil {
		t.Fatal(err)
	}

	report := "report"
	interactionID := "interaction-1"
	if err := UpdateTask(taskID, "COMPLETED", &report, &interactionID); err != nil {
		t.Fatal(err)
	}

	task, err := GetTask(taskID)
	if err != nil {
		t.Fatal(err)
	}
	if task == nil {
		t.Fatal("GetTask returned nil")
	}
	if task.Query != "query" || task.Status != "COMPLETED" || task.Report.String != report {
		t.Fatalf("GetTask() = %+v", task)
	}

	tasks, err := GetRecentTasks(10)
	if err != nil {
		t.Fatal(err)
	}
	if len(tasks) != 1 || tasks[0].ID != taskID || tasks[0].InteractionID.String != interactionID {
		t.Fatalf("GetRecentTasks() = %+v", tasks)
	}
}

func TestUpdateTaskWithoutInteractionID(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "history.db")
	resetTestDB(t, dbPath)

	taskID, err := SaveTask("query without interaction", "model-b", nil, nil)
	if err != nil {
		t.Fatal(err)
	}

	report := "failed report"
	if err := UpdateTask(taskID, "FAILED", &report, nil); err != nil {
		t.Fatal(err)
	}

	task, err := GetTask(taskID)
	if err != nil {
		t.Fatal(err)
	}
	if task == nil {
		t.Fatal("GetTask returned nil")
	}
	if task.Status != "FAILED" || task.Report.String != report {
		t.Fatalf("GetTask() = %+v", task)
	}
}

func TestGetTaskNotFound(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "history.db")
	resetTestDB(t, dbPath)

	if _, err := GetDB(); err != nil {
		t.Fatal(err)
	}

	task, err := GetTask(999999)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if task != nil {
		t.Fatalf("expected nil for non-existent task, got %+v", task)
	}
}

func TestGetRecentTasksLimitsAndOrder(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "history.db")
	resetTestDB(t, dbPath)

	for i := 1; i <= 5; i++ {
		q := "query " + string(rune('0'+i))
		if _, err := SaveTask(q, "model", nil, nil); err != nil {
			t.Fatal(err)
		}
	}

	tasks, err := GetRecentTasks(3)
	if err != nil {
		t.Fatal(err)
	}
	if len(tasks) != 3 {
		t.Fatalf("expected 3 tasks, got %d", len(tasks))
	}

	tasksAll, err := GetRecentTasks(10)
	if err != nil {
		t.Fatal(err)
	}
	if len(tasksAll) != 5 {
		t.Fatalf("expected 5 tasks, got %d", len(tasksAll))
	}

	tasksZero, err := GetRecentTasks(0)
	if err != nil {
		t.Fatal(err)
	}
	if len(tasksZero) != 0 {
		t.Fatalf("expected 0 tasks, got %d", len(tasksZero))
	}
}

func TestGetDBCreatesPrivateDatabaseFile(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "nested", "history.db")
	resetTestDB(t, dbPath)

	if _, err := GetDB(); err != nil {
		t.Fatal(err)
	}

	info, err := os.Stat(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if got := info.Mode().Perm(); got != 0600 {
		t.Fatalf("database mode = %o, want 0600", got)
	}
}

func TestGetDBExistingDirectoryPermissions(t *testing.T) {
	tmpDir := t.TempDir()
	dbDir := filepath.Join(tmpDir, "existing_dir")
	if err := os.Mkdir(dbDir, 0755); err != nil {
		t.Fatal(err)
	}
	dbPath := filepath.Join(dbDir, "history.db")
	resetTestDB(t, dbPath)

	if _, err := GetDB(); err != nil {
		t.Fatal(err)
	}

	dirInfo, err := os.Stat(dbDir)
	if err != nil {
		t.Fatal(err)
	}
	if got := dirInfo.Mode().Perm(); got != 0700 {
		t.Fatalf("dbDir mode = %o, want 0700", got)
	}
}

func TestGetDBRejectsSymlinks(t *testing.T) {
	tmpDir := t.TempDir()
	realDBPath := filepath.Join(tmpDir, "real.db")
	symlinkPath := filepath.Join(tmpDir, "symlink.db")

	if err := os.Symlink(realDBPath, symlinkPath); err != nil {
		t.Fatal(err)
	}

	resetTestDB(t, symlinkPath)

	_, err := GetDB()
	if err == nil {
		t.Fatal("expected GetDB to fail when dbPath is a symlink")
	}

	expectedErrMsg := "is not a regular file"
	if err.Error() == "" || !strings.Contains(err.Error(), expectedErrMsg) {
		t.Fatalf("expected error containing %q, got: %v", expectedErrMsg, err)
	}
}

func BenchmarkGetRecentTasks(b *testing.B) {
	dbPath := filepath.Join(b.TempDir(), "bench.db")
	ResetDBForTesting()
	oldPath := config.DbPath
	config.DbPath = dbPath
	defer func() {
		ResetDBForTesting()
		config.DbPath = oldPath
	}()

	for i := 0; i < 100; i++ {
		interaction := "inter-" + string(rune('0'+i))
		parent := "parent-123"
		if _, err := SaveTask("query string for benchmark", "model-name", &interaction, &parent); err != nil {
			b.Fatal(err)
		}
	}

	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		tasks, err := GetRecentTasks(100)
		if err != nil {
			b.Fatal(err)
		}
		if len(tasks) != 100 {
			b.Fatalf("got %d tasks, want 100", len(tasks))
		}
	}
}
