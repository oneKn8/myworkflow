package cmd

import (
	"fmt"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/sources"
	"github.com/spf13/cobra"
)

var fetchCmd = &cobra.Command{
	Use:   "fetch",
	Short: "Fetch latest stats from all configured sources",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Fetching analytics data...")

		umamiURL, _ := cmd.Flags().GetString("umami-url")
		umamiToken, _ := cmd.Flags().GetString("umami-token")
		umamiSiteID, _ := cmd.Flags().GetString("umami-site-id")
		devtoKey, _ := cmd.Flags().GetString("devto-key")

		if umamiURL != "" && umamiToken != "" && umamiSiteID != "" {
			stats, err := sources.FetchUmami(umamiURL, umamiToken, umamiSiteID)
			if err != nil {
				fmt.Printf("Umami fetch error: %v\n", err)
			} else {
				fmt.Printf("Umami: %d pageviews, %d visitors\n", stats.Pageviews, stats.Visitors)
			}
		}

		if devtoKey != "" {
			articles, err := sources.FetchDevTo(devtoKey)
			if err != nil {
				fmt.Printf("Dev.to fetch error: %v\n", err)
			} else {
				totalViews := 0
				totalReactions := 0
				for _, a := range articles {
					totalViews += a.Views
					totalReactions += a.Reactions
				}
				fmt.Printf("Dev.to: %d articles, %d views, %d reactions\n",
					len(articles), totalViews, totalReactions)
			}
		}

		fmt.Println("Done.")
		return nil
	},
}

func init() {
	fetchCmd.Flags().String("umami-url", "", "Umami API URL")
	fetchCmd.Flags().String("umami-token", "", "Umami API token")
	fetchCmd.Flags().String("umami-site-id", "", "Umami website ID")
	fetchCmd.Flags().String("devto-key", "", "Dev.to API key")

	rootCmd.AddCommand(fetchCmd)
}
