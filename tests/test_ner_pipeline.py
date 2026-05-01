"""
test_ner_pipeline.py
--------------------
Unit tests for NER pipeline module.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ner_pipeline import extract_entities


def test_extract_entities_basic() -> None:
    """Test basic entity extraction."""
    text = "Apple Inc. reported earnings of $89.5 billion in Q3 2024."
    result = extract_entities(text, "test_001")

    assert result["article_id"] == "test_001"
    assert result["text"] == text
    assert isinstance(result["entities"], list)
    assert "processed_at" in result
    # At least some entities should be found
    assert len(result["entities"]) > 0


def test_extract_entities_confidence_scoring() -> None:
    """Test that confidence scores are computed and within valid range."""
    text = "Fed Chair Jerome Powell said rates at 5.5% as of Tuesday."
    result = extract_entities(text, "test_002")

    for entity in result["entities"]:
        assert 0.0 <= entity["confidence"] <= 1.0
        assert "needs_review" in entity
        assert isinstance(entity["needs_review"], bool)


def test_extract_entities_empty_text() -> None:
    """Test handling of empty text."""
    result = extract_entities("", "test_empty")
    assert result["article_id"] == "test_empty"
    assert result["entities"] == []
    assert result["needs_review"] is False


def test_run_pipeline_output_files() -> None:
    """Test that pipeline creates expected output files."""
    from ner_pipeline import run_pipeline

    articles = [
        {"id": "test_1", "text": "Microsoft announced a deal with Activision."},
        {"id": "test_2", "text": "The S&P 500 fell 1.3% on the news."},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "ner_output.jsonl"
        run_pipeline(articles, output_path=str(output_path))

        # Verify output files created
        assert output_path.exists(), f"NER output file not created: {output_path}"
        assert Path(tmpdir).joinpath("review_queue.jsonl").exists(), "Review queue not created"

        # Verify output is valid JSONL
        lines = output_path.read_text().splitlines()
        assert len(lines) == len(articles), f"Expected {len(articles)} lines, got {len(lines)}"

        for line in lines:
            record = json.loads(line)
            assert "article_id" in record
            assert "entities" in record
            assert "needs_review" in record
