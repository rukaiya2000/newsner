"""
config.py
---------
Load and manage configuration from config.yaml.
Provides type-safe access to pipeline settings.
"""

from pathlib import Path
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
    """Load config.yaml from project root."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f) or {}

# Global config instance (loaded once on import)
CONFIG = load_config()

# Convenience accessors
def get_confidence_threshold() -> float:
    threshold = CONFIG.get("ner", {}).get("confidence_threshold", 0.75)
    return float(threshold)

def get_entity_types() -> set[str]:
    entities = CONFIG.get("ner", {}).get("entity_types", [])
    return set(entities)

def get_queries() -> list[str]:
    queries = CONFIG.get("data", {}).get("queries", [])
    return list(queries) if queries else []

def get_output_path(key: str) -> str:
    path = CONFIG.get("output", {}).get(key, f"output/{key}")
    return str(path)

def get_logging_level() -> str:
    level = CONFIG.get("logging", {}).get("level", "INFO")
    return str(level)
