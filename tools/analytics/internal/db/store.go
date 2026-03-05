package db

import (
	"database/sql"
	"os"
	"path/filepath"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

const schema = `
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    metric TEXT NOT NULL,
    value INTEGER NOT NULL,
    recorded_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS article_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    recorded_at TEXT DEFAULT (datetime('now')),
    UNIQUE(platform, article_id, recorded_at)
);
`

func Open() (*sql.DB, error) {
	home, _ := os.UserHomeDir()
	dbPath := filepath.Join(home, ".config", "myworkflow", "analytics.db")

	if err := os.MkdirAll(filepath.Dir(dbPath), 0o755); err != nil {
		return nil, err
	}

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	if _, err := db.Exec(schema); err != nil {
		return nil, err
	}

	return db, nil
}

func SaveSnapshot(db *sql.DB, source, metric string, value int) error {
	_, err := db.Exec(
		"INSERT INTO snapshots (source, metric, value) VALUES (?, ?, ?)",
		source, metric, value,
	)
	return err
}

func SaveArticleStat(db *sql.DB, platform, articleID, title, url string, views, reactions, comments int) error {
	now := time.Now().Format("2006-01-02")
	_, err := db.Exec(
		`INSERT OR REPLACE INTO article_stats (platform, article_id, title, url, views, reactions, comments, recorded_at)
		 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		platform, articleID, title, url, views, reactions, comments, now,
	)
	return err
}

type SnapshotRow struct {
	Source     string
	Metric    string
	Value     int
	RecordedAt string
}

func LatestSnapshots(db *sql.DB) ([]SnapshotRow, error) {
	rows, err := db.Query(`
		SELECT source, metric, value, recorded_at
		FROM snapshots
		WHERE id IN (
			SELECT MAX(id) FROM snapshots GROUP BY source, metric
		)
		ORDER BY source, metric`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []SnapshotRow
	for rows.Next() {
		var r SnapshotRow
		if err := rows.Scan(&r.Source, &r.Metric, &r.Value, &r.RecordedAt); err != nil {
			return nil, err
		}
		result = append(result, r)
	}
	return result, nil
}

type ArticleRow struct {
	Platform  string
	Title     string
	URL       string
	Views     int
	Reactions int
	Comments  int
}

func TopArticles(db *sql.DB, limit int) ([]ArticleRow, error) {
	rows, err := db.Query(`
		SELECT platform, title, url, views, reactions, comments
		FROM article_stats
		WHERE recorded_at = (SELECT MAX(recorded_at) FROM article_stats)
		ORDER BY views DESC
		LIMIT ?`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []ArticleRow
	for rows.Next() {
		var r ArticleRow
		if err := rows.Scan(&r.Platform, &r.Title, &r.URL, &r.Views, &r.Reactions, &r.Comments); err != nil {
			return nil, err
		}
		result = append(result, r)
	}
	return result, nil
}

type PeriodSummary struct {
	Source   string
	Metric  string
	Current int
	Previous int
	Delta    int
}

func PeriodComparison(db *sql.DB, days int) ([]PeriodSummary, error) {
	cutoff := time.Now().AddDate(0, 0, -days).Format("2006-01-02 15:04:05")
	prevCutoff := time.Now().AddDate(0, 0, -days*2).Format("2006-01-02 15:04:05")

	query := `
		SELECT source, metric,
			COALESCE((SELECT value FROM snapshots s2 WHERE s2.source = s1.source AND s2.metric = s1.metric AND s2.recorded_at >= ? ORDER BY recorded_at DESC LIMIT 1), 0) as current_val,
			COALESCE((SELECT value FROM snapshots s3 WHERE s3.source = s1.source AND s3.metric = s1.metric AND s3.recorded_at >= ? AND s3.recorded_at < ? ORDER BY recorded_at DESC LIMIT 1), 0) as prev_val
		FROM (SELECT DISTINCT source, metric FROM snapshots) s1
		ORDER BY source, metric`

	rows, err := db.Query(query, cutoff, prevCutoff, cutoff)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []PeriodSummary
	for rows.Next() {
		var r PeriodSummary
		if err := rows.Scan(&r.Source, &r.Metric, &r.Current, &r.Previous); err != nil {
			return nil, err
		}
		r.Delta = r.Current - r.Previous
		result = append(result, r)
	}
	return result, nil
}
