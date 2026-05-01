"""
Web UI for NewsNER pipeline.
Flask app serving the NER dashboard.
"""

import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import get_entity_types, get_confidence_threshold
from ner_pipeline import extract_entities

app = Flask(__name__)
CORS(app)


@app.route("/")
def index() -> str:
    """Render the dashboard."""
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config() -> dict[str, any]:
    """Get current configuration."""
    return jsonify({
        "entity_types": sorted(list(get_entity_types())),
        "confidence_threshold": get_confidence_threshold(),
    })


@app.route("/api/extract", methods=["POST"])
def extract() -> dict[str, any]:
    """Extract entities from submitted text."""
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        result = extract_entities(text, "web_input")
        return jsonify({
            "entities": result["entities"],
            "needs_review": result["needs_review"],
            "stats": {
                "total_entities": len(result["entities"]),
                "high_confidence": sum(1 for e in result["entities"] if e["confidence"] >= 0.9),
                "needs_review": sum(1 for e in result["entities"] if e["needs_review"]),
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health() -> dict[str, str]:
    """Health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5002)
