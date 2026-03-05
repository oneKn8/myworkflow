package cmd

import (
	"fmt"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/dashboard"
	"github.com/oneKn8/myworkflow/tools/analytics/internal/db"
	"github.com/spf13/cobra"
)

var dashboardCmd = &cobra.Command{
	Use:   "dashboard",
	Short: "Show analytics dashboard",
	RunE: func(cmd *cobra.Command, args []string) error {
		store, err := db.Open()
		if err != nil {
			return fmt.Errorf("failed to open database: %w", err)
		}
		defer store.Close()

		return dashboard.Render(store)
	},
}

func init() {
	rootCmd.AddCommand(dashboardCmd)
}
