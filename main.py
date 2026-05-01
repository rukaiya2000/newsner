"""
main.py
--------
CLI entrypoint for the NewsNER pipeline.

Usage:
    python main.py fetch              # Fetch articles (uses cache if exists)
    python main.py run                # Run NER on cached articles
    python main.py export             # Export review queue to Label Studio format
    python main.py agreement          # Compute inter-annotator agreement metrics
    python main.py all                # Run full pipeline end-to-end
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agreement import analyze_error_patterns, compute_agreement
from fetcher import fetch_all
from label_studio_export import to_label_studio
from logger import get_logger
from ner_pipeline import run_pipeline

logger = get_logger(__name__)


def cmd_fetch() -> None:
    api_key = os.getenv("NEWSAPI_KEY")
    articles = fetch_all(api_key=api_key)
    logger.info(f"Ready: {len(articles)} articles in data/articles_cache.json")


def cmd_run() -> None:
    cache = Path("data/articles_cache.json")
    if not cache.exists():
        logger.error("No article cache found. Run: python main.py fetch")
        return
    articles = json.loads(cache.read_text())
    run_pipeline(articles)


def cmd_export() -> None:
    ner_out = Path("annotations/ner_output.jsonl")
    if not ner_out.exists():
        logger.error("No NER output found. Run: python main.py run")
        return
    to_label_studio(str(ner_out))


def cmd_agreement() -> None:
    model_path = "annotations/ner_output.jsonl"
    human_path = "annotations/human_annotations.jsonl"
    for p in [model_path, human_path]:
        if not Path(p).exists():
            logger.error(f"Missing: {p}")
            return
    metrics = compute_agreement(model_path, human_path)
    errors = analyze_error_patterns(model_path, human_path)

    report = {"agreement_metrics": metrics, "error_count": len(errors)}
    Path("docs/agreement_report.json").parent.mkdir(parents=True, exist_ok=True)
    Path("docs/agreement_report.json").write_text(json.dumps(report, indent=2))
    logger.info("Report saved to docs/agreement_report.json")


def cmd_all() -> None:
    cmd_fetch()
    cmd_run()
    cmd_export()


COMMANDS = {
    "fetch": cmd_fetch,
    "run": cmd_run,
    "export": cmd_export,
    "agreement": cmd_agreement,
    "all": cmd_all,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd not in COMMANDS:
        logger.error(f"Unknown command: {cmd}")
        logger.error(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd]()
