# NewsNER Web UI

A professional Flask-based web dashboard for the NewsNER pipeline. Extract named entities from text with a beautiful, interactive interface.

## Features

✅ **Real-time Entity Extraction** — Paste text and instantly extract named entities  
✅ **Confidence Scoring** — Visual confidence bars for each entity (0-100%)  
✅ **Statistics Dashboard** — Total entities, high confidence count, review queue  
✅ **Color-Coded Labels** — Entity types color-coded for quick visual scanning  
✅ **Responsive Design** — Works on desktop, tablet, and mobile  
✅ **Fast API** — Flask backend with CORS support for future integrations  

## Running the Web UI

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python3 app.py
```

Output:
```
* Running on http://127.0.0.1:5000
```

### 3. Open in Browser
Visit: **http://localhost:5000**

## Usage

1. **Paste Text** — Enter news articles, financial reports, or any text in the textarea
2. **Extract Entities** — Click "Extract Entities" or press `Ctrl+Enter`
3. **Review Results** — See entities with confidence scores and statistics
4. **Filter by Type** — Legend shows all entity types (ORG, PERSON, DATE, MONEY, etc.)

## Architecture

### Backend (Flask)

**File:** `app.py`

**Endpoints:**
- `GET /` — Render the dashboard
- `GET /api/config` — Get entity types and confidence threshold
- `GET /api/health` — Health check
- `POST /api/extract` — Extract entities from text

**Response Format:**
```json
{
  "entities": [
    {
      "text": "Apple Inc.",
      "label": "ORG",
      "start": 0,
      "end": 10,
      "confidence": 1.0,
      "needs_review": false
    }
  ],
  "stats": {
    "total_entities": 6,
    "high_confidence": 4,
    "needs_review": 0
  }
}
```

### Frontend (HTML/CSS/JavaScript)

**Files:**
- `templates/index.html` — Dashboard layout
- `static/style.css` — Responsive styling with dark-friendly design
- `static/script.js` — Interactive features and API integration

## Customization

### Change Entity Types

Edit `config.yaml`:
```yaml
ner:
  entity_types:
    - SPECIES
    - DIET_TYPE
    - HABITAT
    - TRAIT
```

Restart the server — the UI will update automatically.

### Change Confidence Threshold

Edit `config.yaml`:
```yaml
ner:
  confidence_threshold: 0.80  # Default is 0.75
```

### Custom Styling

Edit `static/style.css` to change colors, fonts, or layout. Update entity colors in:
```javascript
// In static/script.js
const ENTITY_COLORS = {
    ORG: '#dbeafe',      // Blue
    PERSON: '#ddd6fe',   // Purple
    ...
};
```

## API Examples

### Extract Entities
```bash
curl -X POST http://localhost:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple Inc. reported earnings of $89.5 billion in Q3 2024."
  }'
```

### Get Configuration
```bash
curl http://localhost:5000/api/config
```

## Performance

- **Extraction Speed:** ~85 articles/second (100+ articles in <2 seconds)
- **Browser Responsiveness:** Real-time feedback with loading state
- **Memory Usage:** Minimal (Flask + spaCy model = ~500MB)

## Deployment

For production, replace Flask's development server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use Docker:
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN python3 -m spacy download en_core_web_sm
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

**Port already in use:**
```bash
lsof -i :5000
kill -9 <PID>
```

**spaCy model not found:**
```bash
python3 -m spacy download en_core_web_sm
```

**CORS errors:**
Flask-CORS is enabled. If integrating with external domains, update `app.py`:
```python
CORS(app, resources={r"/api/*": {"origins": "https://yourdomain.com"}})
```

## Tech Stack

- **Backend:** Flask 3.0+, Python 3.9+
- **NER:** spaCy 3.7+
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **API:** JSON REST
- **Styling:** CSS Grid, Flexbox, Custom Properties

## License

MIT
