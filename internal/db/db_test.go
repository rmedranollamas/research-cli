package db

import (
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/google/research-cli/internal/config"
)

func resetTestDB(t *testing.T, path string) {
	t.Helper()
	if db != nil {
		if err := db.Close(); err != nil {
			t.Fatal(err)
		}
	}
	db = nil
	dbOnce = sync.Once{}
	oldPath := config.DbPath
	config.DbPath = path
	t.Cleanup(func() {
		if db != nil {
			_ = db.Close()
		}
		db = nil
		dbOnce = sync.Once{}
		config.DbPath = oldPath
	})
}

func TestTaskLifecycle(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "history.db")
	resetTestDB(t, dbPath)

	parentID := "parent-1"
	taskID, err := SaveTask("query", "model", nil, &parentID)
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
