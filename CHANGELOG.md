# Changelog

All notable changes to this project will be documented in this file.

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