# Release Notes - v1.0.0

## Summary

Teams Search Stack 1.0.0 delivers a production-ready, self-hosted search infrastructure with Docker Compose orchestration. This release focuses on stability and ease of deployment.

## Highlights

### Docker-Based Deployment
The stack now runs as containerized services with Docker Compose, providing:
- Isolated service boundaries
- Easy scaling and updates
- Consistent behavior across environments

### Dual API Endpoints
Two complementary APIs are available:
1. **Search API** (`/api/search`) - Returns structured search results in JSON
2. **Scraper API** (`/scrape`) - Firecrawl-compatible web content extraction

### Zero-Configuration Startup
```bash
docker compose up -d
# Services are immediately available on ports 8082, 3000, 9090
```

## Service Matrix

| Container | Purpose | Ports | Dependencies |
|-----------|---------|-------|--------------|
| caddy_proxy | Reverse proxy | 8082 | searxng |
| searxng | Search engine | internal:8080 | - |
| search_api | JSON API | 9090 | searxng |
| scraper_api | Web scraper | 3000 | - |
| redis | Queue | internal:6379 | - |

## Breaking Changes

- The `local-search` CLI command from the Python package now requires Docker
- Previous pip-install approach deprecated in favor of `docker compose up -d`

## Migration Guide

If upgrading from the Python-only version:

```bash
# Stop old service
pkill -f "searx.webapp" 2>/dev/null || true

# Pull latest and start Docker stack
git pull
docker compose up -d
```

## Known Issues

- Search engines may return rate-limited responses if heavily used
- JSON format endpoint (`format=json`) returns HTML from upstream SearXNG; use port 9090 Search API instead