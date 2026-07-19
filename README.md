# Teams Search Stack

Self-hosted SearXNG metasearch engine with a Docker Compose deployment, a JSON
Search API, and a Firecrawl-compatible scraper API. Private, no third-party API
keys required for the query path.

Current build: **v1.1.0** (see [CHANGELOG.md](./CHANGELOG.md)).

## Stack Architecture (Docker Compose)

```
┌──────────────────────────────────────────────────────────────┐
│                          host (ubuntu-pc)                      │
│                                                                │
│  Port 8082 ── caddy_proxy ──┐                                  │
│       │                     │ forwards X-Real-IP / X-Forwarded-│
│       └─ HTML Search UI     ▼                                  │
│                          SearXNG (internal :8080)              │
│                               ▲                                 │
│  Port 9090 ── search_api ────┘  (native /search?format=json)   │
│       │  /api/search?q=QUERY  -> {"query","results","total"}   │
│                                                                │
│  Port 3000 ── scraper_api (Firecrawl-compatible)               │
│       │  /scrape  (markdown)   /extract (structured)           │
│       │  /api/v0/health                                       │
│                                                                │
│  No Redis — removed (declared but never consumed).            │
└──────────────────────────────────────────────────────────────┘
```

All containers share the `search_net` Docker network (172.20.0.0/16).
SearXNG, search_api and scraper_api communicate internally; only caddy (8082),
search_api (9090) and scraper_api (3000) publish host ports.

## Quick Start

```bash
git clone https://github.com/bogdandragosaccesa/teams-search
cd teams-search
cp .env.example .env        # edit if you want API keys / custom secret
SEARXNG_SECRET_KEY="$(openssl rand -hex 32)" docker compose up -d --build

# Check services
docker compose ps
curl -s "http://localhost:9090/api/search?q=python" | python3 -m json.tool
```

## API Endpoints

### Search API (JSON)
```bash
curl "http://localhost:9090/api/search?q=python"
# -> {"query": "python", "total_results": 25, "results": [{"title","url","content","engine","score"}]}
```
- Optional Bearer auth when `SEARCH_API_KEY` is set in the environment:
  `curl -H "Authorization: Bearer $SEARCH_API_KEY" ...`. Open (no key) by default.

### Scraper API (Firecrawl-compatible)
```bash
curl -X POST http://localhost:3000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}'
# -> {"data": {"markdown": "..."}}
```
Other routes: `/extract` (POST, structured field extraction),
`/api/v0/health` (GET, 200 = alive).

### Web UI
```bash
open http://localhost:8082
```

## Services

| Service      | Port (host) | Description |
|--------------|-------------|-------------|
| `caddy_proxy`| 8082        | Reverse proxy + static UI to SearXNG |
| `search_api` | 9090        | JSON API over SearXNG native `format=json` |
| `scraper_api`| 3000        | Firecrawl-compatible web scraper / extractor |
| `searxng`    | internal    | SearXNG search core (no host port) |

## Configuration

- `config/sxng_config.yml` — SearXNG settings. **Mounted at
  `/etc/searxng/settings.yml`** (SearXNG's actual path; a `searxng.yml` name is
  silently ignored). Allows `html`/`json`/`csv`/`rss` output formats;
  `server.bind_address: 0.0.0.0`.
- `config/limiter.toml` — bot detection config. `link_token = false`,
  `filter_link_local = false`, `trusted_proxies` includes the Docker subnet.
  Mounted at `/etc/searxng/limiter.toml`.
- `config/Caddyfile` — Caddy reverse proxy; forwards `X-Real-IP` /
  `X-Forwarded-For` to SearXNG for client-IP attribution.

## Environment Variables

```yaml
SEARXNG_SECRET_KEY=...          # random; openssl rand -hex 32
SEARXNG_URL=http://searxng:8080 # internal SearXNG endpoint (search_api)
SEARCH_API_KEY=                 # optional Bearer token for /api/search
SCRAPER_API_KEY=                # optional Bearer token for scraper_api
SEARXNG_TRUSTED_IP=172.20.0.1   # spoofed client IP for internal requests
```

## Security & Hardening

This stack ships with **dev-friendly defaults** (bot detection off via
`limiter.toml`, no API keys, a per-deploy random `secret_key`). Those are fine
on a trusted single-host LAN but **must not** be used on an internet-exposed host.

Before exposing it (e.g. on a public domain behind your reverse proxy / SSO):

1. Set a persistent random `SEARXNG_SECRET_KEY` (not regenerated per start).
2. Set `SEARCH_API_KEY` / `SCRAPER_API_KEY` so the APIs require a Bearer token.
3. Do **not** publish ports 3000/9090 directly — front them with Caddy/your SSO.
4. Tighten `trusted_proxies` in `config/limiter.toml` before production use.

Copy `.env.example` → `.env` and edit. `.env` is git-ignored.

## Hermes Integration

This stack is wired as a private search/scrape backend for Hermes (the AI agent
on this host). See the `teams-search-hermes-wiring` skill: Hermes queries
`localhost:9090` / `localhost:3000` directly — no egress to external search
providers. (No TLS required for localhost; an internal domain with a self-signed
cert is optional and not yet added.)

## What changed in v1.1.0 (vs v1.0.0)

- **403 fixed** — root cause was `search.formats` allowing only `html`;
  `format=json` now permitted. Also corrected the config mount path
  (`settings.yml`, not `searxng.yml`) and `bind_address: 0.0.0.0`.
- `search_api` uses SearXNG's native `/search?format=json` (no HTML scraping).
- `secret_key` and rate-limit/bypass flags are environment-driven.
- Both APIs run under **gunicorn** (production WSGI).
- Healthchecks on every service; stack self-heals.
- Redis removed (declared but never consumed).

## License

MIT License
