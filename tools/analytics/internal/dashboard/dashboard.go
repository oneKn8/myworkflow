package dashboard

import (
	"fmt"

	"github.com/oneKn8/myworkflow/tools/analytics/internal/aggregator"
)

func Render(summary aggregator.Summary) {
	fmt.Println("=== Content Analytics ===")
	fmt.Println()
	fmt.Printf("Blog (Umami 30d)\n")
	fmt.Printf("  Pageviews:  %d\n", summary.UmamiPageviews)
	fmt.Printf("  Visitors:   %d\n", summary.UmamiVisitors)
	fmt.Println()
	fmt.Printf("Dev.to\n")
	fmt.Printf("  Articles:   %d\n", summary.DevToArticles)
	fmt.Printf("  Views:      %d\n", summary.DevToViews)
	fmt.Printf("  Reactions:  %d\n", summary.DevToReactions)
	fmt.Println()
	fmt.Println("(TUI dashboard coming soon)")
}
