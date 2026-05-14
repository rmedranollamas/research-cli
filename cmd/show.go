package cmd

import (
	"fmt"
	"strconv"

	"github.com/google/research-cli/internal/db"
	"github.com/google/research-cli/internal/ui"
	"github.com/spf13/cobra"
)

var showCmd = &cobra.Command{
	Use:   "show [task_id]",
	Short: "Show details and report for a specific research task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		taskID, err := strconv.ParseInt(args[0], 10, 64)
		if err != nil {
			return fmt.Errorf("invalid task ID: %s", args[0])
		}

		task, err := db.GetTask(taskID)
		if err != nil {
			return err
		}

		if task == nil {
			return fmt.Errorf("task not found: %d", taskID)
		}

		fmt.Printf("Task ID: %d\n", task.ID)
		fmt.Printf("Query: %s\n", task.Query)
		fmt.Printf("Status: %s\n", task.Status)

		if task.Report.Valid && task.Report.String != "" {
			ui.PrintReport(task.Report.String)
			output, _ := cmd.Flags().GetString("output")
			force, _ := cmd.Flags().GetBool("force")
			if err := saveReportIfRequested(task.Report.String, output, force); err != nil {
				return err
			}
		} else {
			fmt.Println("\nNo report available for this task.")
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(showCmd)
	showCmd.Flags().StringP("output", "o", "", "Output file to save the report")
	showCmd.Flags().BoolP("force", "f", false, "Force overwrite output file")
}
