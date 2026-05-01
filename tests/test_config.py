"""
test_config.py
--------------
Unit tests for configuration loading.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import (
    CONFIG,
    get_confidence_threshold,
    get_entity_types,
    get_logging_level,
    get_queries,
)


def test_config_loads() -> None:
    """Test that config.yaml is loaded successfully."""
    assert CONFIG is not None
    assert isinstance(CONFIG, dict)


def test_confidence_threshold() -> None:
    """Test confidence threshold accessor."""
    threshold = get_confidence_threshold()
    assert isinstance(threshold, (int, float))
    assert 0.0 <= threshold <= 1.0


def test_entity_types() -> None:
    """Test entity types accessor."""
    entity_types = get_entity_types()
    assert isinstance(entity_types, set)
    assert len(entity_types) > 0
    # Verify they are strings
    for etype in entity_types:
        assert isinstance(etype, str)


def test_queries() -> None:
    """Test queries accessor."""
    queries = get_queries()
    assert isinstance(queries, list)
    assert len(queries) > 0
    for q in queries:
        assert isinstance(q, str)


def test_logging_level() -> None:
    """Test logging level accessor."""
    level = get_logging_level()
    assert isinstance(level, str)
    assert level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
