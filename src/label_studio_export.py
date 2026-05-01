"""
label_studio_export.py
-----------------------
Converts NER pipeline output into Label Studio import format (JSON).
Also converts Label Studio export back into our ground-truth JSONL schema.

Label Studio docs: https://labelstud.io/guide/tasks.html
"""

import json
from pathlib import Path
from typing import Any

from logger import get_logger

logger = get_logger(__name__)


def to_label_studio(ner_jsonl_path: str, output_path: str = "annotations/label_studio_import.json") -> list[dict[str, Any]]:
    """
    Convert ner_output.jsonl → Label Studio import JSON.
    Each article becomes a task; model annotations become pre-annotations.
    Only articles flagged needs_review=True are included (saves reviewer time).
    """
    tasks = []
    with open(ner_jsonl_path) as f:
        for line in f:
            record = json.loads(line)
            if not record.get("needs_review"):
                continue

            # Build pre-annotations from model output
            predictions = []
            for ent in record["entities"]:
                if not ent["needs_review"]:
                    continue
                predictions.append({
                    "from_name": "label",
                    "to_name": "text",
                    "type": "labels",
                    "value": {
                        "start": ent["start"],
                        "end": ent["end"],
                        "text": ent["text"],
                        "labels": [ent["label"]],
                    },
                    "score": ent["confidence"],
                })

            tasks.append({
                "data": {
                    "text": record["text"],
                    "article_id": record["article_id"],
                },
                "predictions": [{"model_version": "spacy-newsner-v1", "result": predictions}],
            })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(tasks, indent=2))
    logger.info(f"Exported {len(tasks)} tasks to {output_path}")
    return tasks


def from_label_studio(export_path: str, output_path: str = "annotations/human_annotations.jsonl") -> list[dict[str, Any]]:
    """
    Convert Label Studio export JSON → our ground-truth JSONL format.
    Preserves article_id so agreement.py can align model vs human annotations.
    """
    data = json.loads(Path(export_path).read_text())
    records = []

    for task in data:
        article_id = task.get("data", {}).get("article_id", task.get("id", "unknown"))
        text = task.get("data", {}).get("text", "")

        # Collect completed annotations (first annotator's submission)
        entities = []
        annotations = task.get("annotations", [])
        if annotations:
            for result in annotations[0].get("result", []):
                val = result.get("value", {})
                start = val.get("start")
                end = val.get("end")
                labels = val.get("labels", [])
                span_text = val.get("text", text[start:end] if start is not None else "")
                if labels:
                    entities.append({
                        "text": span_text,
                        "label": labels[0],
                        "start": start,
                        "end": end,
                        "confidence": 1.0,  # human-confirmed = full confidence
                        "needs_review": False,
                    })

        record = {
            "article_id": article_id,
            "text": text,
            "entities": entities,
            "needs_review": False,
            "annotator": "human",
        }
        records.append(record)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    logger.info(f"Converted {len(records)} human-annotated tasks to {output_path}")
    return records
