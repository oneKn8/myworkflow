package sources

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type DevToArticle struct {
	ID        int    `json:"id"`
	Title     string `json:"title"`
	URL       string `json:"url"`
	Views     int    `json:"page_views_count"`
	Reactions int    `json:"positive_reactions_count"`
	Comments  int    `json:"comments_count"`
	Published string `json:"published_at"`
}

func FetchDevTo(apiKey string) ([]DevToArticle, error) {
	url := "https://dev.to/api/articles/me/published?per_page=100"

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("api-key", apiKey)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("dev.to API returned %d: %s", resp.StatusCode, string(body))
	}

	var articles []DevToArticle
	if err := json.NewDecoder(resp.Body).Decode(&articles); err != nil {
		return nil, err
	}

	return articles, nil
}
