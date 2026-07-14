# Teams Search Stack

Self-hosted SearXNG search engine with Docker Compose deployment, featuring a Firecrawl-compatible scraper API.

## Stack Architecture (Docker Compose)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Port 8082 ── caddy_proxy ── SearXNG (internal 8080)   │
│       │                                                 │
│       └─ HTML Search UI                                 │
│                                                         │
│  Port 9090 ── search_api ── searxng:8080              │
│       │                                                 │
│       └─ `/api/search?q=QUERY` (JSON response)          │
│                                                         │
│  Port 3000 ── scraper_api                              │
│       │                                                 │
│       └─ `/scrape` (Firecrawl-compatible)              │
│                                                         │
│  Redis (internal) ── Queue for background jobs           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and run
git clone https://github.com/bogdandragosaccesa/teams-search
cd teams-search
docker compose up -d

# Check services
docker compose ps
```

## API Endpoints

### Search API (JSON)
```bash
curl "http://localhost:9090/api/search?q=python&format=json"
# Returns: {"query": "python", "total_results": 30, "results": [...]}
```

### Scraper API (Firecrawl-compatible)
```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
# Returns: {"success": true, "data": {"markdown": "...", "title": "..."}}
```

### Web UI
```bash
open http://localhost:8082
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `caddy_proxy` | 8082 | Reverse proxy to SearXNG |
| `search_api` | 9090 | JSON API wrapper (parses HTML → JSON) |
| `scraper_api` | 3000 | Firecrawl-compatible web scraper |
| `searxng` | internal | Search engine core |
| `redis` | internal | Job queue |

## Configuration

- `config/limiter.toml` - Bot detection bypass (wildcard `0.0.0.0/0` for local dev)
- `config/sxng_config.yml` - SearXNG engine configuration
- `config/Caddyfile` - Caddy reverse proxy rules

## Environment Variables

```yaml
SEARXNG_URL=http://searxng:8080    # Internal SearXNG endpoint
RATE_LIMIT=0                        # Disable rate limiting
BYPASS_BLOCKLIST=true                 # Bypass bot detection
```

## License

MIT License