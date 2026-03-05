package cmd

import (
	"fmt"
	"os"
	"strconv"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/db"
	"github.com/oneKn8/myworkflow/tools/analytics/internal/sources"
	"github.com/spf13/cobra"
)

var fetchCmd = &cobra.Command{
	Use:   "fetch",
	Short: "Fetch latest stats from all configured sources and save to DB",
	RunE: func(cmd *cobra.Command, args []string) error {
		store, err := db.Open()
		if err != nil {
			return fmt.Errorf("failed to open database: %w", err)
		}
		defer store.Close()

		umamiURL := envOrFlag(cmd, "umami-url", "UMAMI_BASE_URL")
		umamiToken := envOrFlag(cmd, "umami-token", "UMAMI_TOKEN")
		umamiSiteID := envOrFlag(cmd, "umami-site-id", "UMAMI_WEBSITE_ID")
		devtoKey := envOrFlag(cmd, "devto-key", "DEVTO_API_KEY")

		fetched := 0

		if umamiURL != "" && umamiToken != "" && umamiSiteID != "" {
			stats, err := sources.FetchUmami(umamiURL, umamiToken, umamiSiteID)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Umami: %v\n", err)
			} else {
				db.SaveSnapshot(store, "umami", "pageviews", stats.Pageviews)
				db.SaveSnapshot(store, "umami", "visitors", stats.Visitors)
				db.SaveSnapshot(store, "umami", "bounces", stats.Bounces)
				fmt.Printf("Umami: %d pageviews, %d visitors\n", stats.Pageviews, stats.Visitors)
				fetched++
			}
		}

		if devtoKey != "" {
			articles, err := sources.FetchDevTo(devtoKey)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Dev.to: %v\n", err)
			} else {
				totalViews := 0
				totalReactions := 0
				for _, a := range articles {
					totalViews += a.Views
					totalReactions += a.Reactions
					db.SaveArticleStat(store, "devto", strconv.Itoa(a.ID), a.Title, a.URL, a.Views, a.Reactions, a.Comments)
				}
				db.SaveSnapshot(store, "devto", "total_views", totalViews)
				db.SaveSnapshot(store, "devto", "total_reactions", totalReactions)
				db.SaveSnapshot(store, "devto", "article_count", len(articles))
				fmt.Printf("Dev.to: %d articles, %d views, %d reactions\n",
					len(articles), totalViews, totalReactions)
				fetched++
			}
		}

		if fetched == 0 {
			fmt.Println("No sources configured. Set environment variables or pass flags.")
			fmt.Println("  UMAMI_BASE_URL, UMAMI_TOKEN, UMAMI_WEBSITE_ID")
			fmt.Println("  DEVTO_API_KEY")
		} else {
			fmt.Printf("Saved %d source(s) to database.\n", fetched)
		}

		return nil
	},
}

func envOrFlag(cmd *cobra.Command, flag, envKey string) string {
	val, _ := cmd.Flags().GetString(flag)
	if val != "" {
		return val
	}
	return os.Getenv(envKey)
}

func init() {
	fetchCmd.Flags().String("umami-url", "", "Umami API URL (or UMAMI_BASE_URL)")
	fetchCmd.Flags().String("umami-token", "", "Umami API token (or UMAMI_TOKEN)")
	fetchCmd.Flags().String("umami-site-id", "", "Umami website ID (or UMAMI_WEBSITE_ID)")
	fetchCmd.Flags().String("devto-key", "", "Dev.to API key (or DEVTO_API_KEY)")

	rootCmd.AddCommand(fetchCmd)
}
