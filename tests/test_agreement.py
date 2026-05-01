"""
test_agreement.py
-----------------
Unit tests for inter-annotator agreement module.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agreement import _span_key, analyze_error_patterns, compute_agreement


def test_span_key() -> None:
    """Test span key generation."""
    entity = {"text": "Apple", "label": "ORG", "start": 0, "end": 5, "confidence": 0.95}
    key = _span_key(entity)

    assert isinstance(key, tuple)
    assert len(key) == 3
    assert key == (0, 5, "ORG")


def test_compute_agreement_identical_annotations() -> None:
    """Test agreement when model and human annotations are identical."""
    model_data = [
        {
            "article_id": "doc_1",
            "text": "Apple Inc. is in California.",
            "entities": [
                {"text": "Apple Inc.", "label": "ORG", "start": 0, "end": 10, "confidence": 0.95},
                {"text": "California", "label": "GPE", "start": 18, "end": 28, "confidence": 0.88},
            ],
        }
    ]

    human_data = [
        {
            "article_id": "doc_1",
            "text": "Apple Inc. is in California.",
            "entities": [
                {"text": "Apple Inc.", "label": "ORG", "start": 0, "end": 10, "confidence": 1.0},
                {"text": "California", "label": "GPE", "start": 18, "end": 28, "confidence": 1.0},
            ],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.jsonl"
        human_path = Path(tmpdir) / "human.jsonl"

        model_path.write_text("\n".join(json.dumps(r) for r in model_data))
        human_path.write_text("\n".join(json.dumps(r) for r in human_data))

        result = compute_agreement(str(model_path), str(human_path))

        assert "kappa" in result
        assert result["articles_compared"] == 1
        assert result["agreed"] == 2  # Both entities match


def test_compute_agreement_no_overlap() -> None:
    """Test agreement when there's no overlapping articles."""
    model_data = [{"article_id": "doc_1", "text": "Test", "entities": []}]
    human_data = [{"article_id": "doc_2", "text": "Test", "entities": []}]

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.jsonl"
        human_path = Path(tmpdir) / "human.jsonl"

        model_path.write_text(json.dumps(model_data[0]))
        human_path.write_text(json.dumps(human_data[0]))

        result = compute_agreement(str(model_path), str(human_path))

        # Should return empty dict when no overlap
        assert result == {}


def test_analyze_error_patterns_false_positives() -> None:
    """Test error pattern detection for false positives."""
    model_data = [
        {
            "article_id": "doc_1",
            "text": "Stock prices rose.",
            "entities": [
                {"text": "Stock", "label": "NOUN", "start": 0, "end": 5},
                {"text": "prices", "label": "NOUN", "start": 6, "end": 12},
            ],
        }
    ]

    human_data = [
        {
            "article_id": "doc_1",
            "text": "Stock prices rose.",
            "entities": [
                # Human only tagged one (stock), not prices
                {"text": "Stock", "label": "ORG", "start": 0, "end": 5},
            ],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.jsonl"
        human_path = Path(tmpdir) / "human.jsonl"

        model_path.write_text(json.dumps(model_data[0]))
        human_path.write_text(json.dumps(human_data[0]))

        errors = analyze_error_patterns(str(model_path), str(human_path))

        # Should detect false positive (model tagged "prices" but human didn't)
        false_positives = [e for e in errors if e["type"] == "false_positive"]
        assert len(false_positives) > 0
