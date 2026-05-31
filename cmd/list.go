package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/google/research-cli/internal/db"
	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List recent research tasks",
	RunE: func(cmd *cobra.Command, args []string) error {
		limit, _ := cmd.Flags().GetInt("limit")
		tasks, err := db.GetRecentTasks(limit)
		if err != nil {
			return err
		}

		if len(tasks) == 0 {
			fmt.Println("No research tasks found.")
			return nil
		}

		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "ID\tQUERY\tSTATUS\tCREATED AT\tINTERACTION ID")
		for _, t := range tasks {
			query := truncateRunes(t.Query, 50)
			fmt.Fprintf(w, "%d\t%s\t%s\t%s\t%s\n", t.ID, query, t.Status, t.CreatedAt, t.InteractionID.String)
		}
		w.Flush()
		return nil
	},
}

func init() {
	rootCmd.AddCommand(listCmd)
	listCmd.Flags().IntP("limit", "n", 20, "Number of tasks to list")
}

func truncateRunes(s string, limit int) string {
	if limit <= 0 {
		return ""
	}

	count := 0
	ellipsisIdx := 0
	for i := range s {
		if count == limit-3 {
			ellipsisIdx = i
		}
		if count == limit {
			if limit <= 3 {
				return s[:i]
			}
			return s[:ellipsisIdx] + "..."
		}
		count++
	}

	return s
}
