"""
ner_pipeline.py
----------------
Runs spaCy NER on fetched articles, flags low-confidence spans,
and writes results to JSONL for human review in Label Studio.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import spacy
from tqdm import tqdm

from config import get_confidence_threshold, get_entity_types
from logger import get_logger

logger = get_logger(__name__)

# Load model — falls back gracefully if large model not installed
def load_model() -> spacy.Language:
    for model in ("en_core_web_lg", "en_core_web_md", "en_core_web_sm"):
        try:
            return spacy.load(model)
        except OSError:
            continue
    raise RuntimeError("No spaCy model found. Run: python -m spacy download en_core_web_sm")

nlp = load_model()

# Load entity types and confidence threshold from config.yaml
TARGET_LABELS = get_entity_types()
CONFIDENCE_THRESHOLD = get_confidence_threshold()


def extract_entities(text: str, article_id: str) -> dict[str, Any]:
    """
    Run NER on a single article text.
    Returns structured result with entities and a flag for low-confidence spans.
    """
    doc = nlp(text)

    entities = []
    needs_review = False

    for ent in doc.ents:
        if ent.label_ not in TARGET_LABELS:
            continue

        # spaCy doesn't expose per-span confidence natively,
        # so we approximate using a heuristic: short or ambiguous spans score lower
        confidence = _estimate_confidence(ent)

        entity = {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
            "confidence": round(confidence, 3),
            "needs_review": confidence < CONFIDENCE_THRESHOLD,
        }
        entities.append(entity)

        if entity["needs_review"]:
            needs_review = True

    return {
        "article_id": article_id,
        "text": text,
        "entities": entities,
        "needs_review": needs_review,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def _estimate_confidence(ent: spacy.tokens.Span) -> float:
    """
    Heuristic confidence score.
    - Short spans (1 token) are less certain
    - All-caps or numeric-only spans penalized slightly
    - Otherwise full confidence
    """
    score = 1.0
    if len(ent) == 1:
        score -= 0.15
    if ent.text.isupper() and len(ent.text) <= 4:
        score -= 0.10
    if any(tok.is_digit for tok in ent):
        score -= 0.05
    return max(0.0, min(1.0, score))


def run_pipeline(articles: list[dict[str, Any]], output_path: str = "annotations/ner_output.jsonl") -> list[dict[str, Any]]:
    """
    Process a list of article dicts: [{"id": ..., "text": ...}]
    Writes full results to JSONL, low-confidence to a separate review queue.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    review_path = output_file.parent / "review_queue.jsonl"

    results = []
    review_count = 0

    with open(output_file, "w") as f_out, open(review_path, "w") as f_review:
        for article in tqdm(articles, desc="Processing articles", unit="article"):
            result = extract_entities(article["text"], article["id"])
            results.append(result)
            f_out.write(json.dumps(result) + "\n")

            if result["needs_review"]:
                f_review.write(json.dumps(result) + "\n")
                review_count += 1

    logger.info(f"Processed {len(results)} articles.")
    logger.info(f"  → {review_count} flagged for human review.")
    logger.info(f"  → Full output: {output_file}")
    logger.info(f"  → Review queue: {review_path}")
    return results
