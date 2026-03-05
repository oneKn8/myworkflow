package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/db"
	"github.com/spf13/cobra"
)

var reportCmd = &cobra.Command{
	Use:   "report",
	Short: "Show analytics summary from stored data",
	RunE: func(cmd *cobra.Command, args []string) error {
		store, err := db.Open()
		if err != nil {
			return fmt.Errorf("failed to open database: %w", err)
		}
		defer store.Close()

		format, _ := cmd.Flags().GetString("format")

		snapshots, err := db.LatestSnapshots(store)
		if err != nil {
			return err
		}

		articles, err := db.TopArticles(store, 10)
		if err != nil {
			return err
		}

		if format == "json" {
			out := map[string]any{
				"snapshots": snapshots,
				"top_articles": articles,
			}
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(out)
		}

		// Table output
		if len(snapshots) == 0 {
			fmt.Println("No data yet. Run 'analytics fetch' first.")
			return nil
		}

		fmt.Println("=== Latest Metrics ===")
		fmt.Println()
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "SOURCE\tMETRIC\tVALUE\tRECORDED\n")
		fmt.Fprintf(w, "------\t------\t-----\t--------\n")
		for _, s := range snapshots {
			fmt.Fprintf(w, "%s\t%s\t%d\t%s\n", s.Source, s.Metric, s.Value, s.RecordedAt)
		}
		w.Flush()

		if len(articles) > 0 {
			fmt.Println()
			fmt.Println("=== Top Articles ===")
			fmt.Println()
			w = tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
			fmt.Fprintf(w, "PLATFORM\tTITLE\tVIEWS\tREACTIONS\n")
			fmt.Fprintf(w, "--------\t-----\t-----\t---------\n")
			for _, a := range articles {
				title := a.Title
				if len(title) > 40 {
					title = title[:37] + "..."
				}
				fmt.Fprintf(w, "%s\t%s\t%d\t%d\n", a.Platform, title, a.Views, a.Reactions)
			}
			w.Flush()
		}

		return nil
	},
}

func init() {
	reportCmd.Flags().String("format", "table", "Output format: table or json")

	rootCmd.AddCommand(reportCmd)
}
