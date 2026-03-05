package aggregator

import "github.com/oneKn8/myworkflow/tools/analytics/internal/sources"

type Summary struct {
	UmamiPageviews int
	UmamiVisitors  int
	DevToArticles  int
	DevToViews     int
	DevToReactions int
}

func Aggregate(umami *sources.UmamiStats, devto []sources.DevToArticle) Summary {
	s := Summary{}

	if umami != nil {
		s.UmamiPageviews = umami.Pageviews
		s.UmamiVisitors = umami.Visitors
	}

	if devto != nil {
		s.DevToArticles = len(devto)
		for _, a := range devto {
			s.DevToViews += a.Views
			s.DevToReactions += a.Reactions
		}
	}

	return s
}
