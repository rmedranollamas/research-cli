package db

import (
	"database/sql"
	"os"
	"path/filepath"
	"sync"

	"github.com/google/research-cli/internal/config"
	_ "modernc.org/sqlite"
)

var (
	db     *sql.DB
	dbOnce sync.Once
)

type Task struct {
	ID            int
	InteractionID sql.NullString
	ParentID      sql.NullString
	Query         string
	Model         string
	Status        string
	Report        sql.NullString
	CreatedAt     string
}

func GetDB() (*sql.DB, error) {
	var err error
	dbOnce.Do(func() {
		dbPath := config.DbPath
		dbDir := filepath.Dir(dbPath)

		if dbDir != "" {
			_, statErr := os.Stat(dbDir)
			if os.IsNotExist(statErr) {
				err = os.MkdirAll(dbDir, 0700)
				if err != nil {
					return
				}
			} else if statErr != nil {
				err = statErr
				return
			} else {
				// Secure TOCTOU fallback using os package
				f, openErr := os.Open(dbDir)
				if openErr != nil {
					err = openErr
					return
				}
				if chmodErr := f.Chmod(0700); chmodErr != nil {
					_ = f.Close()
					err = chmodErr
					return
				}
				if closeErr := f.Close(); closeErr != nil {
					err = closeErr
					return
				}
			}
		}

		db, err = sql.Open("sqlite", dbPath)
		if err != nil {
			return
		}

		if err = db.Ping(); err != nil {
			return
		}

		if err = os.Chmod(dbPath, 0600); err != nil {
			return
		}

		if err = initSchema(db); err != nil {
			return
		}
	})

	return db, err
}

func initSchema(db *sql.DB) error {
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS research_tasks (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			interaction_id TEXT UNIQUE, 
			parent_id TEXT,
			query TEXT,
			model TEXT,
			status TEXT,
			report TEXT,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		return err
	}

	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at ON research_tasks (created_at)")
	return err
}

func SaveTask(query, model string, interactionID, parentID *string) (int64, error) {
	conn, err := GetDB()
	if err != nil {
		return 0, err
	}

	res, err := conn.Exec(
		"INSERT INTO research_tasks (query, model, interaction_id, status, parent_id) VALUES (?, ?, ?, ?, ?)",
		query, model, interactionID, "PENDING", parentID,
	)
	if err != nil {
		return 0, err
	}

	return res.LastInsertId()
}

func UpdateTask(taskID int64, status string, report, interactionID *string) error {
	conn, err := GetDB()
	if err != nil {
		return err
	}

	if interactionID != nil {
		_, err = conn.Exec(
			"UPDATE research_tasks SET status = ?, report = ?, interaction_id = ? WHERE id = ?",
			status, report, interactionID, taskID,
		)
	} else {
		_, err = conn.Exec(
			"UPDATE research_tasks SET status = ?, report = ? WHERE id = ?",
			status, report, taskID,
		)
	}
	return err
}

func GetTask(taskID int64) (*Task, error) {
	conn, err := GetDB()
	if err != nil {
		return nil, err
	}

	row := conn.QueryRow("SELECT query, report, status FROM research_tasks WHERE id = ?", taskID)
	var t Task
	err = row.Scan(&t.Query, &t.Report, &t.Status)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	t.ID = int(taskID)
	return &t, nil
}

func GetRecentTasks(limit int) ([]Task, error) {
	conn, err := GetDB()
	if err != nil {
		return nil, err
	}

	rows, err := conn.Query(
		"SELECT id, query, status, created_at, interaction_id FROM research_tasks ORDER BY created_at DESC LIMIT ?",
		limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []Task
	for rows.Next() {
		var t Task
		err := rows.Scan(&t.ID, &t.Query, &t.Status, &t.CreatedAt, &t.InteractionID)
		if err != nil {
			return nil, err
		}
		tasks = append(tasks, t)
	}
	return tasks, nil
}
