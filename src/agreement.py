"""
agreement.py
-------------
Computes inter-annotator agreement (Cohen's Kappa) between:
  - The model's auto-annotations (annotator A)
  - A human reviewer's corrections (annotator B)

Also logs common extraction error patterns — mirrors the internship's
requirement to document inter-annotator agreement and refine the pipeline.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from logger import get_logger

logger = get_logger(__name__)


def load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _span_key(entity: dict[str, Any]) -> tuple[int, int, str]:
    """Unique key for a span: (start, end, label)."""
    return (entity["start"], entity["end"], entity["label"])


def compute_agreement(model_path: str, human_path: str) -> dict[str, Any]:
    """
    Compare model annotations vs human corrections at span level.
    Returns Cohen's Kappa and a breakdown of agreement per entity type.

    Both files are JSONL where each line = one article's annotation result.
    Human file should have the same article_ids as model file.
    """
    model_records = {r["article_id"]: r for r in load_jsonl(model_path)}
    human_records = {r["article_id"]: r for r in load_jsonl(human_path)}

    common_ids = set(model_records) & set(human_records)
    if not common_ids:
        logger.warning("No overlapping article IDs between model and human annotations.")
        return {}

    # Per-label counts
    label_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"agree": 0, "model_only": 0, "human_only": 0})
    total_agree = total_model_only = total_human_only = 0

    for aid in common_ids:
        m_spans = {_span_key(e) for e in model_records[aid]["entities"]}
        h_spans = {_span_key(e) for e in human_records[aid]["entities"]}

        for span in m_spans & h_spans:
            label_stats[span[2]]["agree"] += 1
            total_agree += 1

        for span in m_spans - h_spans:
            label_stats[span[2]]["model_only"] += 1
            total_model_only += 1

        for span in h_spans - m_spans:
            label_stats[span[2]]["human_only"] += 1
            total_human_only += 1

    total = total_agree + total_model_only + total_human_only
    if total == 0:
        return {"kappa": 0.0, "label_stats": {}}

    # Cohen's Kappa (simplified binary: agree vs disagree)
    p_observed = total_agree / total
    # Expected agreement by chance (assuming both annotators are symmetric)
    p_model = (total_agree + total_model_only) / total
    p_human = (total_agree + total_human_only) / total
    p_expected = p_model * p_human + (1 - p_model) * (1 - p_human)

    kappa = (p_observed - p_expected) / (1 - p_expected) if p_expected < 1 else 1.0

    logger.info(f"=== Inter-Annotator Agreement ({len(common_ids)} articles) ===")
    logger.info(f"Cohen's Kappa: {kappa:.3f}  ({_interpret_kappa(kappa)})")
    logger.info(f"Agreed spans : {total_agree}")
    logger.info(f"Model only   : {total_model_only}")
    logger.info(f"Human only   : {total_human_only}")
    logger.info("Per-label breakdown:")
    for label, counts in sorted(label_stats.items()):
        tot = counts["agree"] + counts["model_only"] + counts["human_only"]
        acc = counts["agree"] / tot if tot else 0
        logger.info(f"  {label:<10}  agree={counts['agree']:>4}  model_only={counts['model_only']:>4}  human_only={counts['human_only']:>4}  accuracy={acc:.1%}")

    return {
        "kappa": round(kappa, 4),
        "articles_compared": len(common_ids),
        "total_spans": total,
        "agreed": total_agree,
        "model_only": total_model_only,
        "human_only": total_human_only,
        "label_stats": {k: dict(v) for k, v in label_stats.items()},
    }


def analyze_error_patterns(model_path: str, human_path: str) -> list[dict[str, Any]]:
    """
    Identify systematic extraction errors:
    - False positives (model tagged, human didn't)
    - False negatives (human tagged, model missed)
    - Label mismatches (same span, different label)
    """
    model_records = {r["article_id"]: r for r in load_jsonl(model_path)}
    human_records = {r["article_id"]: r for r in load_jsonl(human_path)}

    errors = []
    for aid in set(model_records) & set(human_records):
        m_map = {(e["start"], e["end"]): e for e in model_records[aid]["entities"]}
        h_map = {(e["start"], e["end"]): e for e in human_records[aid]["entities"]}

        for span, m_ent in m_map.items():
            if span not in h_map:
                errors.append({"type": "false_positive", "article_id": aid, "entity": m_ent})
            elif h_map[span]["label"] != m_ent["label"]:
                errors.append({
                    "type": "label_mismatch",
                    "article_id": aid,
                    "model_label": m_ent["label"],
                    "human_label": h_map[span]["label"],
                    "text": m_ent["text"],
                })

        for span, h_ent in h_map.items():
            if span not in m_map:
                errors.append({"type": "false_negative", "article_id": aid, "entity": h_ent})

    # Summarize by error type
    from collections import Counter
    counts = Counter(e["type"] for e in errors)
    logger.info(f"=== Error Pattern Summary ({len(errors)} total errors) ===")
    for etype, n in counts.most_common():
        logger.info(f"  {etype:<20}: {n}")

    return errors


def _interpret_kappa(kappa: float) -> str:
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
