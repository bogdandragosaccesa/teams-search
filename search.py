#!/usr/bin/env python3
"""search.py - JSON search API wrapper for SearXNG.

Uses SearXNG's native JSON endpoint (?format=json) instead of scraping HTML,
so it is robust against UI/layout changes. Returns a normalized result list.
"""

import os
import logging
import requests as http_client
from flask import Flask, request, jsonify

SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://searxng:8080")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.environ.get("PORT", 9090))
# Require a shared API key when API_KEY is set (empty = open, for trusted LAN only).
API_KEY = os.environ.get("SEARCH_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
log = logging.getLogger("search-api")

app = Flask(__name__)


def check_auth():
    """Optional API key validation (Bearer token). Open if API_KEY unset."""
    if not API_KEY:
        return True
    auth = request.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip() == API_KEY


def parse_search_json(payload):
    """Normalize SearXNG JSON results into a stable shape."""
    results = []
    for r in payload.get("results", []) or []:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "")[:500],
            "engine": r.get("engine", "unknown"),
            "score": r.get("score"),
        })
    return results


@app.route("/")
def index():
    return jsonify({"service": "teams-search", "status": "running"})


@app.route("/health")
def health():
    return jsonify({"healthy": True})


@app.route("/api/search")
def do_search():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    try:
        resp = http_client.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json"},
            timeout=30,
            headers={"X-Forwarded-For": "172.20.0.1", "X-Real-IP": "172.20.0.1"},
        )
        if resp.status_code != 200:
            return jsonify({"error": f"SearXNG HTTP {resp.status_code}"}), resp.status_code

        data = resp.json()
        results = parse_search_json(data)
        return jsonify({
            "query": query,
            "total_results": len(results),
            "results": results,
        })
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500


if __name__ == "__main__":
    print(f"Search API on :{LISTEN_PORT}")
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=False)
