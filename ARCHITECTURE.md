# Architecture

This document describes the deployed topology of the Teams Search Stack as of
build **v1.1.0**.

## Container topology

```
┌──────────────────────────────────────────────────────────────────┐
│ host: ubuntu-pc                                                    │
│                                                                    │
│  browser / Hermes (localhost)                                      │
│        │                                                           │
│        ├───────────────► :8082  caddy_proxy                         │
│        │                      │ reverse_proxy + static UI          │
│        │                      ▼                                    │
│        │                  searxng:8080  (SearXNG core)             │
│        │                      ▲                                    │
│        ├───────────────► :9090  search_api                         │
│        │                      │ GET /search?format=json            │
│        │                      ▼                                    │
│        │                  searxng:8080                            │
│        │                                                           │
│        └───────────────► :3000  scraper_api                        │
│                              (Firecrawl-compatible; standalone)    │
└──────────────────────────────────────────────────────────────────┘
```

## Services

| Container    | Image / Build        | Host port | Internal | Role |
|--------------|----------------------|-----------|----------|------|
| `caddy_proxy`| `caddy:latest`       | 8082      | 80/443   | Reverse proxy + Search UI |
| `search_api` | local (`Dockerfile.search`) | 9090 | 9090 | JSON search wrapper over SearXNG |
| `scraper_api`| local (`Dockerfile`) | 3000      | 3000     | Firecrawl-compatible scrape/extract |
| `searxng`    | `ghcr.io/searxng/searxng:latest` | — | 8080 | Metasearch core |

No Redis. No database. State is ephemeral (SearXNG in-memory + Valkey inside
the searxng image if configured).

## Network

All containers join the `search_net` Docker bridge network (subnet
`172.20.0.0/16`). Container-to-container calls use service DNS names
(`searxng`, `search_api`, `scraper_api`, `caddy_proxy`). Only `caddy_proxy`
(8082), `search_api` (9090) and `scraper_api` (3000) publish to the host.

## Request flows

### Web search (UI)
`browser → caddy_proxy:8082 → searxng:8080/search?format=html`
Caddy injects `X-Real-IP` / `X-Forwarded-For` (`{remote_host}`) so SearXNG
attributes the client IP.

### JSON search (API / Hermes)
`client → search_api:9090/api/search?q=Q`
`search_api → searxng:8080/search?format=json` (with spoofed
`X-Real-IP`/`X-Forwarded-For` = `SEARXNG_TRUSTED_IP`, default `172.20.0.1`).
Response is normalized to `{"query","results":[...],"total_results"}`.

### Scrape
`client → scraper_api:3000/scrape` (POST `{url, formats:[markdown]}`)
Returns `{"data": {"markdown": "..."}}`. Standalone; does not touch SearXNG.

## Configuration files

| File                   | Mounted at                    | Purpose |
|------------------------|-------------------------------|---------|
| `config/sxng_config.yml` | `/etc/searxng/settings.yml` | SearXNG settings (formats, bind, engines) |
| `config/limiter.toml`    | `/etc/searxng/limiter.toml`  | Bot detection (disabled for self-host) |
| `config/Caddyfile`       | `/etc/caddy/Caddyfile`       | Reverse proxy rules |

> Path note: SearXNG reads `settings.yml`, **not** `searxng.yml`. A wrong
> filename is silently ignored and the image defaults are used instead.

## Bot detection (self-hosted)

`limiter.toml` sets `link_token = false` and `filter_link_local = false`;
`trusted_proxies` includes `172.20.0.0/16`. This prevents the JSON API from
being 403'd on internal container-to-container traffic. Do not enable
`link_token` unless you also front requests with a session cookie.

## Secrets

- `SEARXNG_SECRET_KEY` — random per deploy (`openssl rand -hex 32`). Injected
  into `sxng_config.yml` via `${SEARXNG_SECRET_KEY:...}` env interpolation.
- `SEARCH_API_KEY` / `SCRAPER_API_KEY` — optional Bearer tokens; empty = open
  on the LAN.

## Hermes wiring

Hermes (same host) reaches the stack at `localhost:9090` (search) and
`localhost:3000` (scrape). No TLS required for localhost. Documented in the
`teams-search-hermes-wiring` skill.
