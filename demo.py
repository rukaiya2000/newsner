"""
demo.py
--------
Runs the NER pipeline on real articles fetched from NewsAPI or RSS feeds.
No API key required — falls back to RSS if NewsAPI unavailable.
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv not installed, use environment variables

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fetcher import fetch_all
from label_studio_export import to_label_studio
from logger import get_logger
from ner_pipeline import run_pipeline

logger = get_logger(__name__)

SAMPLE_ARTICLES = [
    {
        "id": "demo_001",
        "text": (
            "Apple Inc. reported record earnings of $89.5 billion in Q3 2024, "
            "beating analyst expectations by 12%. CEO Tim Cook said the company "
            "would expand operations in Germany and India next year."
        ),
    },
    {
        "id": "demo_002",
        "text": (
            "The Federal Reserve raised interest rates by 25 basis points on Wednesday, "
            "pushing the benchmark rate to 5.5%. Fed Chair Jerome Powell signaled "
            "that further hikes remain on the table amid persistent inflation."
        ),
    },
    {
        "id": "demo_003",
        "text": (
            "Microsoft announced a $68.7 billion acquisition of Activision Blizzard, "
            "marking one of the largest deals in the tech sector. The deal, approved "
            "by UK regulators in October, is expected to close by December 31."
        ),
    },
    {
        "id": "demo_004",
        "text": (
            "SEC launched an investigation into Elon Musk's acquisition of Twitter, "
            "now rebranded as X Corp, citing potential violations of disclosure rules. "
            "Shares of X fell 8% following the announcement."
        ),
    },
    {
        "id": "demo_005",
        "text": (
            "Goldman Sachs and JPMorgan Chase both reported lower-than-expected profits "
            "for the second quarter, as rising costs and weaker trading revenues weighed "
            "on results. The S&P 500 fell 1.3% on the news."
        ),
    },
]


if __name__ == "__main__":
    logger.info("=== NewsNER Demo — Fetching Real Articles ===")

    api_key = os.getenv("NEWSAPI_KEY")
    if api_key:
        logger.info("Using NewsAPI (API key detected)")
    else:
        logger.info("No NEWSAPI_KEY set — using RSS feeds (free, no auth required)")

    try:
        articles = fetch_all(api_key=api_key, use_cache=False)
        if not articles:
            raise ValueError("No articles fetched")
        logger.info(f"Fetched {len(articles)} articles from live sources")
    except Exception as e:
        logger.warning(f"Failed to fetch live data: {e}")
        logger.info("Falling back to sample articles...")
        articles = SAMPLE_ARTICLES

    results = run_pipeline(articles, output_path="annotations/ner_output.jsonl")

    print("\n--- Sample entity output ---")
    for r in results[:2]:
        print(f"\nArticle: {r['article_id']}")
        for ent in r["entities"]:
            flag = " ⚑ review" if ent["needs_review"] else ""
            print(f"  [{ent['label']:8}] {ent['text']:<30} (conf={ent['confidence']:.2f}){flag}")

    to_label_studio("annotations/ner_output.jsonl")
    print("\nDone. Check annotations/ for output files.")
