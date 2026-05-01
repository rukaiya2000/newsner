"""
fetcher.py
-----------
Retrieves documents via REST APIs (NewsAPI primary, RSS fallback) with caching.

This module demonstrates the pattern used in research data pipelines:
- Query external data source (NewsAPI ≈ PubMed API)
- De-duplicate results
- Cache locally for reproducibility
- Format consistently for downstream processing

Swap the API and queries for any domain: PubMed for biology, ArXiv for ML, etc.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm

from config import CONFIG
from logger import get_logger

logger = get_logger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2/everything"

# Load configuration
data_config = CONFIG.get("data", {})
RSS_FEEDS = data_config.get("rss", {}).get("feeds", [])
QUERIES = data_config.get("queries", [])


def fetch_newsapi(query: str, api_key: str, days_back: int = 7, max_articles: int = 20) -> list[dict[str, str]]:
    """Fetch articles from NewsAPI for a given query."""
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "from": from_date,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": max_articles,
        "apiKey": api_key,
    }
    resp = requests.get(NEWSAPI_BASE, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for item in data.get("articles", []):
        text = " ".join(filter(None, [item.get("title"), item.get("description"), item.get("content")]))
        if not text.strip():
            continue
        articles.append({
            "id": _make_id(item.get("url", text)),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", {}).get("name", "unknown"),
            "published_at": item.get("publishedAt", ""),
            "text": text.strip(),
            "query": query,
        })
    return articles


def fetch_rss(feed_url: str, max_articles: int = 10) -> list[dict[str, str]]:
    """Fetch articles from an RSS feed (no API key required)."""
    import xml.etree.ElementTree as ET
    resp = requests.get(feed_url, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    articles = []
    for item in root.iter("item"):
        title = item.findtext("title", "")
        desc = item.findtext("description", "")
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "")
        text = f"{title}. {desc}".strip()
        if not text:
            continue
        articles.append({
            "id": _make_id(link or text),
            "title": title,
            "url": link,
            "source": feed_url,
            "published_at": pub,
            "text": text,
            "query": "rss",
        })
        if len(articles) >= max_articles:
            break
    return articles


def fetch_all(api_key: Optional[str] = None, use_cache: bool = True) -> list[dict[str, str]]:
    """
    Main entry point. Uses NewsAPI if key is available, otherwise falls back to RSS.
    Caches results locally to avoid re-fetching during development.
    """
    cache_path = Path("data/articles_cache.json")
    if use_cache and cache_path.exists():
        logger.info(f"Loading {cache_path} from cache...")
        cached = json.loads(cache_path.read_text())
        return cached if isinstance(cached, list) else []

    all_articles = []
    seen_ids = set()

    if api_key:
        logger.info("Fetching from NewsAPI...")
        for query in tqdm(QUERIES, desc="NewsAPI queries", unit="query"):
            try:
                articles = fetch_newsapi(query, api_key)
                for a in articles:
                    if a["id"] not in seen_ids:
                        all_articles.append(a)
                        seen_ids.add(a["id"])
                logger.info(f"[{query}] → {len(articles)} articles")
            except Exception as e:
                logger.error(f"[{query}] NewsAPI error: {e}")
    else:
        logger.info("No NewsAPI key found — falling back to RSS feeds...")
        for feed in tqdm(RSS_FEEDS, desc="RSS feeds", unit="feed"):
            try:
                articles = fetch_rss(feed)
                for a in articles:
                    if a["id"] not in seen_ids:
                        all_articles.append(a)
                        seen_ids.add(a["id"])
                logger.info(f"[{feed}] → {len(articles)} articles")
            except Exception as e:
                logger.error(f"[{feed}] RSS error: {e}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(all_articles, indent=2))
    logger.info(f"Fetched {len(all_articles)} total articles → saved to {cache_path}")
    return all_articles


def _make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]
