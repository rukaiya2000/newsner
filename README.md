# NewsNER — Human-in-the-Loop NER Pipeline

A domain-agnostic named entity recognition system that extracts structured entities from text sources via APIs, surfaces low-confidence predictions for expert human review, and measures inter-annotator agreement to iteratively improve extraction quality.

**Use cases:** Financial news curation, biological literature mining, biomedical entity extraction, research data collection, scientific knowledge base construction.

## 🌐 Web UI

Interactive dashboard for real-time entity extraction. [Learn more →](WEB_UI.md)

**Quick Start:**
```bash
python3 app.py
# Open http://localhost:5000
```

## Pipeline Overview

```
NewsAPI / RSS Feeds
        ↓
   fetcher.py         ← retrieve articles via REST API
        ↓
  ner_pipeline.py     ← auto-annotate with spaCy, flag low-confidence spans
        ↓
label_studio_export   ← format review queue for Label Studio
        ↓
  [Human Review]      ← annotator corrects / confirms in Label Studio
        ↓
  agreement.py        ← compute Cohen's Kappa, log error patterns
        ↓
 Ground-Truth JSONL   ← versioned dataset in /annotations/
```

## Entity Types

The default configuration extracts financial entities from news:

| Label    | Example                          |
|----------|----------------------------------|
| ORG      | Apple Inc., the Federal Reserve  |
| PERSON   | Jerome Powell, Elon Musk         |
| GPE      | United States, Frankfurt         |
| MONEY    | $4.2 billion, €500M              |
| PERCENT  | 3.5%, down 12 basis points       |
| DATE     | Q3 2024, last Tuesday            |
| EVENT    | FOMC meeting, IPO                |

### Domain Transferability

The architecture is domain-agnostic. To adapt for other domains (e.g., biological data curation):

```python
# In ner_pipeline.py, change TARGET_LABELS:
TARGET_LABELS = {"SPECIES", "DIET_TYPE", "HABITAT", "TRAIT", "BEHAVIOR"}

# In fetcher.py, swap data sources:
QUERIES = ["mammalian diet behavior", "herbivore feeding patterns", ...]
API_BASE = "https://www.ncbi.nlm.nih.gov/entrez/eutils"  # PubMed instead of NewsAPI
```

The entire pipeline (fetch → annotate → review → measure agreement) remains unchanged.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set optional NewsAPI key (falls back to RSS if not set)
export NEWSAPI_KEY=your_key_here

# Run full pipeline
python main.py all

# Or step by step
python main.py fetch       # Fetch & cache articles
python main.py run         # Run NER, write annotations/ner_output.jsonl
python main.py export      # Export review queue → annotations/label_studio_import.json

# After human review in Label Studio, export and save to annotations/human_annotations.jsonl
python main.py agreement   # Compute Cohen's Kappa + error patterns
```

## Human Review Workflow (Label Studio)

1. Install Label Studio: `pip install label-studio`
2. Start: `label-studio start`
3. Create a new project → **Named Entity Recognition** template
4. Import: `annotations/label_studio_import.json`
5. Review and correct the pre-annotations
6. Export as JSON → save to `annotations/human_annotations.jsonl`
7. Run `python main.py agreement`

## Output Files

| File | Description |
|------|-------------|
| `data/articles_cache.json` | Raw fetched documents (source-agnostic) |
| `annotations/ner_output.jsonl` | Model auto-annotations for all documents |
| `annotations/review_queue.jsonl` | Prioritized low-confidence items for expert review |
| `annotations/label_studio_import.json` | Label Studio batch import (ready for annotation) |
| `annotations/human_annotations.jsonl` | Expert-validated ground-truth dataset |
| `docs/agreement_report.json` | Cohen's Kappa, per-label accuracy, error breakdown |

The outputs form a reproducible, versioned dataset suitable for model training or publication with collaborators.

## Confidence Threshold & Human-in-the-Loop

Spans below `0.75` confidence are automatically flagged for expert review. Adjust in `src/ner_pipeline.py`:

```python
CONFIDENCE_THRESHOLD = 0.75  # Configurable per domain
```

This selective review strategy mirrors research workflows where expert annotators validate model predictions rather than annotating from scratch — reducing labeling burden while maintaining data quality.

## Evaluation & Quality Metrics

After human reviewers correct annotations in Label Studio, the pipeline computes:
- **Cohen's Kappa** — agreement between model and human on extracted spans
- **Per-entity-type accuracy** — breakdown by label (e.g., organism detection vs. habitat)
- **Error pattern analysis** — false positives, false negatives, label confusion
- **Confidence calibration** — whether low-confidence predictions align with actual errors

This enables iterative model refinement and confidence threshold tuning.

## Project Structure

```
newsner/
├── main.py                        # CLI entrypoint (chainable pipeline stages)
├── requirements.txt               # spacy, requests, label-studio
├── src/
│   ├── fetcher.py                 # REST API / feed ingestion (swappable sources)
│   ├── ner_pipeline.py            # Transformer NER + confidence heuristics
│   ├── label_studio_export.py     # Annotation platform I/O (format adapter)
│   └── agreement.py               # Inter-annotator agreement metrics + error analysis
├── data/                          # Source documents cache (gitignored)
├── annotations/                   # NER outputs → validated ground-truth
└── docs/                          # Agreement reports + metrics
```

Each module is independent and swappable (e.g., replace spaCy with HuggingFace transformers, or Label Studio with Prodigy).
