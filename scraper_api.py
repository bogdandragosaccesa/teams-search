"""Local Scraper Service (Firecrawl-Compatible)

A self-hosted web scraper that provides Firecrawl-like markdown conversion
for JS-heavy or complex web pages without depending on private registries.

Usage:
    python scraper_api.py --port 3000

Dependencies: flask, requests, beautifulsoup4
"""

import os
import sys
import argparse
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

# Configuration
HOST = "0.0.0.0"
PORT = int(os.environ.get("FIRECRAWL_PORT", 3000))
API_KEY = os.environ.get("API_KEY", "")
SCRAPE_COUNTER = 0

app = Flask(__name__)


def extract_markdown(html, url):
    """Convert raw HTML to clean markdown using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "aside",
                      "[style*='display:none']", "noscript"]):
        tag.decompose()

    # Extract links as markdown bullets
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        text = (a_tag.get_text(strip=True) or "").lower()[:50]
        if text and len(text) > 3:
            links.append(f"  - [{text}]({href})")

    # Get clean body text
    text = soup.get_text(separator="\n", strip=True)

    lines = []
    prev_blank = False
    for line in text.splitlines():
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        lines.append(line)
        prev_blank = is_blank

    content_md = "\n\n".join(lines[:5000])
    links_md = "\n\n---\n\n**Links:**\n" + "\n".join(links[:30]) if links else ""

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url.split("/")[2]
    final_text = f"# {title}\n\n{content_md}{links_md}"

    return final_text.strip()


def fetch_page(url, accept_markdown=True, timeout=30):
    """Fetch a URL and extract content as structured data."""
    result = {"url": url}

    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        resp.raise_for_status()

        if accept_markdown:
            result["markdown"] = extract_markdown(resp.text, url)
        else:
            result["html"] = resp.text[:5000]

    except Exception as exc:
        result["error"] = str(exc)[:200]

    return result


def check_auth():
    """Optional API key validation."""
    if not API_KEY:
        return True
    auth = request.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip() == API_KEY


@app.route("/")
def health():
    return jsonify({
        "status": "ok",
        "version": "1.1.0-local",
        "services": {"scraper": True},
    })


@app.route("/api/v0/health")
def health_check():
    """Compatible health endpoint for Docker compose depends_on."""
    return jsonify({"healthy": True, "count": SCRAPE_COUNTER})


@app.route("/scrape", methods=["POST"])
def scrape_endpoint():
    """Main scrape endpoint - Firecrawl-compatible format."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_url = data.get("url", "")
    formats = data.get("formats", ["markdown"])
    timeout_val = int(data.get("timeout", 30))

    if not target_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    global SCRAPE_COUNTER
    SCRAPE_COUNTER += 1

    page_result = fetch_page(target_url, accept_markdown="markdown" in formats,
                              timeout=timeout_val)

    response_data = {"success": True, "scrape_id": str(SCRAPE_COUNTER)}
    if "error" not in page_result:
        md_content = page_result.get("markdown", "")
        first_line = md_content.split("\n")[0] if md_content else ""
        title = first_line.replace("# ", "") if first_line.startswith("# ") else ""

        response_data["data"] = {
            "status": "succeeded",
            "url": target_url,
            "markdown": md_content,
            "title": title or "",
        }
    else:
        response_data["data"] = {
            "status": "failed",
            "error": page_result.get("error", ""),
        }

    return jsonify(response_data), 200 if "success" in response_data else 500


@app.route("/extract", methods=["POST"])
def extract_endpoint():
    """Alias endpoint for extraction."""
    return scrape_endpoint()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Local self-hosted scraper (Firecrawl-compatible)"
    )
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    print(f"""
  ╔═══════════════════════════════════╗
  ║  Local Scraper Service            ║
  ║  Listening on: http://0.0.0.0:{args.port}  ║
  ╚═══════════════════════════════════╝
""")

    app.run(host="0.0.0.0", port=args.port, debug=False)
