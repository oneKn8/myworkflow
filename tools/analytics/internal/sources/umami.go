package sources

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type UmamiStats struct {
	Pageviews int `json:"pageviews"`
	Visitors  int `json:"visitors"`
	Bounces   int `json:"bounces"`
	TotalTime int `json:"totaltime"`
}

type umamiAPIResponse struct {
	Pageviews struct {
		Value int `json:"value"`
	} `json:"pageviews"`
	Visitors struct {
		Value int `json:"value"`
	} `json:"visitors"`
	Bounces struct {
		Value int `json:"value"`
	} `json:"bounces"`
	TotalTime struct {
		Value int `json:"value"`
	} `json:"totaltime"`
}

func FetchUmami(baseURL, token, siteID string) (*UmamiStats, error) {
	now := time.Now()
	startAt := now.AddDate(0, 0, -30).UnixMilli()
	endAt := now.UnixMilli()

	url := fmt.Sprintf("%s/api/websites/%s/stats?startAt=%d&endAt=%d",
		baseURL, siteID, startAt, endAt)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+token)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("umami API returned %d: %s", resp.StatusCode, string(body))
	}

	var apiResp umamiAPIResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}

	return &UmamiStats{
		Pageviews: apiResp.Pageviews.Value,
		Visitors:  apiResp.Visitors.Value,
		Bounces:   apiResp.Bounces.Value,
		TotalTime: apiResp.TotalTime.Value,
	}, nil
}
