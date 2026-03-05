package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var dashboardCmd = &cobra.Command{
	Use:   "dashboard",
	Short: "Launch interactive TUI dashboard",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Dashboard TUI -- coming soon")
		fmt.Println("Use 'analytics fetch' to pull data first")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(dashboardCmd)
}
