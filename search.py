#!/usr/bin/env python3
"""search.py - HTML-to-JSON search API wrapper for SearXNG"""

import os
import sys
import logging
import requests as http_client
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://searxng:8080")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.environ.get("PORT", 9090))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
log = logging.getLogger("search-api")

app = Flask(__name__)

def parse_search_html(html_content):
    """Extract search results from SearXNG HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    results = []
    for article in soup.find_all("article", class_="result"):
        title_elem = article.find("h3")
        link_elem = article.find("a", class_="url_header")
        content_elem = article.find("p", class_="content")
        
        if title_elem:
            results.append({
                "title": title_elem.get_text(strip=True),
                "url": link_elem["href"] if link_elem else "",
                "content": content_elem.get_text(strip=True)[:500] if content_elem else "",
                "engine": (article.find("span") or {}).get_text(strip=True) if article.find("span") else "unknown"
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
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    try:
        resp = http_client.get(f"{SEARXNG_URL}/search", params={"q": query, "format": "html"}, timeout=30)
        if resp.status_code != 200:
            return jsonify({"error": f"SearXNG HTTP {resp.status_code}"}), resp.status_code
        
        results = parse_search_html(resp.text)
        return jsonify({"query": query, "total_results": len(results), "results": results})
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500

if __name__ == "__main__":
    print(f"Search API on :{LISTEN_PORT}")
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=False)
