package dashboard

import (
	"fmt"
	"strings"
	"text/tabwriter"
	"os"

	"database/sql"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/db"
)

func Render(store *sql.DB) error {
	snapshots, err := db.LatestSnapshots(store)
	if err != nil {
		return err
	}

	articles, err := db.TopArticles(store, 5)
	if err != nil {
		return err
	}

	width := 50
	border := strings.Repeat("=", width)

	fmt.Println(border)
	fmt.Println("  Content Analytics Dashboard")
	fmt.Println(border)
	fmt.Println()

	if len(snapshots) == 0 {
		fmt.Println("  No data. Run 'analytics fetch' first.")
		return nil
	}

	// Group by source
	grouped := make(map[string][]db.SnapshotRow)
	for _, s := range snapshots {
		grouped[s.Source] = append(grouped[s.Source], s)
	}

	for source, metrics := range grouped {
		fmt.Printf("  [%s]\n", strings.ToUpper(source))
		for _, m := range metrics {
			fmt.Printf("    %-20s %d\n", m.Metric, m.Value)
		}
		fmt.Println()
	}

	if len(articles) > 0 {
		fmt.Println("  [TOP ARTICLES]")
		w := tabwriter.NewWriter(os.Stdout, 4, 0, 2, ' ', 0)
		for i, a := range articles {
			title := a.Title
			if len(title) > 35 {
				title = title[:32] + "..."
			}
			fmt.Fprintf(w, "    %d. %s\t%d views\t%d reactions\n", i+1, title, a.Views, a.Reactions)
		}
		w.Flush()
	}

	fmt.Println()
	fmt.Println(border)
	return nil
}
