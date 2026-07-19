# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-07-19

### Fixed
- **Search API 403** — root cause was `search.formats` allowing only `html`;
  `format=json` was rejected by SearXNG with `403 Forbidden`. Now `html`,
  `json`, `csv`, `rss` are permitted.
- **Config silently ignored** — SearXNG reads `/etc/searxng/settings.yml`,
  but the compose mounted `searxng.yml`. Config now mounts at the correct path.
- **Unreachable from other containers** — `server.bind_address` was
  `127.0.0.1` (container loopback); changed to `0.0.0.0`.
- **Bot detection on internal traffic** — `limiter.toml` re-added with
  `link_token = false` and `filter_link_local = false`; mounted at the correct
  path so it is actually loaded.

### Changed
- `search_api` uses SearXNG's native `/search?format=json` endpoint
  (was scraping HTML and brittle).
- `config/sxng_config.yml` based on the image's valid default settings
  (`instance_name: teams-search`); `secret_key` injected via `${SEARXNG_SECRET_KEY}`.
- Both APIs run under **gunicorn** (production WSGI), not the Flask dev server.
- Healthchecks added to every service; stack self-heals.

### Removed
- Redis — declared in compose but never consumed by the code.

### Added
- `ARCHITECTURE.md` documenting the container topology and network.
- Hermes integration note (private localhost search/scrape backend).

## [1.0.0] - 2026-07-14

### Added
- Docker Compose deployment for containerized SearXNG stack
- Caddy reverse proxy (port 8082) for SearXNG web UI
- Search API wrapper (port 9090) with HTML-to-JSON parsing
- Firecrawl-compatible scraper API (port 3000) for web content extraction
- Redis queue service for background job management
- `limiter.toml` with wildcard `0.0.0.0/0` trusted_proxies for development

### Changed
- Replaced direct Python SearXNG execution with Docker-based deployment
- Split services into separate containers for better isolation
- Added beautifulsoup4 dependency for HTML parsing

### Fixed
- Bot detection 403 errors via `trusted_proxies` configuration
- Firecrawl official image removed (required Docker-in-Docker for NuQ stack)
- Scraper API now uses local Python implementation

### Removed
- Direct `local-search` CLI script (moved to Docker)
- Embedded engines in settings (now uses SearXNG defaults)
