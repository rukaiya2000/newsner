/**
 * NewsNER Web UI JavaScript
 * Handles form submission, API calls, and result rendering
 */

const API_BASE = '/api';
let config = null;

// Color mapping for entity types
const ENTITY_COLORS = {
    ORG: '#dbeafe',
    PERSON: '#ddd6fe',
    GPE: '#d1fae5',
    MONEY: '#fef3c7',
    PERCENT: '#fecaca',
    DATE: '#f5d4e6',
    EVENT: '#ccfbf1',
};

// Example texts
const EXAMPLES = {
    financial: "Apple Inc. reported record earnings of $89.5 billion in Q3 2024, beating analyst expectations by 12%. CEO Tim Cook said the company would expand operations in Germany and India next year. The stock rose 3.2% on the news.",
    tech: "Google announced its new AI assistant, Gemini, which will be available on Pixel phones starting next month. The company also revealed plans to open a new research center in Mountain View, California. Competing with OpenAI's ChatGPT, the technology aims to revolutionize how people interact with their devices.",
    general: "The United Nations held a summit in Geneva on climate change. Secretary-General António Guterres urged world leaders to take action before 2030. Delegates from 195 countries attended the three-day conference, which concluded with a commitment to reduce carbon emissions by 50 percent."
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    try {
        // Fetch configuration
        const response = await fetch(`${API_BASE}/config`);
        config = await response.json();

        // Render legend
        renderLegend(config.entity_types);

        // Attach event listeners
        document.getElementById('extract-btn').addEventListener('click', handleExtract);
        document.getElementById('input-text').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') handleExtract();
        });

        // Tab navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', handleTabClick);
        });

        // Example buttons
        document.querySelectorAll('.btn-example').forEach(btn => {
            btn.addEventListener('click', handleExampleClick);
        });
    } catch (error) {
        showError('Failed to load configuration');
    }
}

/**
 * Handle tab navigation
 */
function handleTabClick(e) {
    const tab = e.target.getAttribute('data-tab');

    // Update active button
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');

    // Update active pane
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    document.getElementById(`${tab}-tab`).classList.add('active');
}

/**
 * Handle example button click
 */
function handleExampleClick(e) {
    const example = e.target.getAttribute('data-example');
    document.getElementById('input-text').value = EXAMPLES[example];
    document.getElementById('input-text').focus();
}

/**
 * Render the entity type legend
 */
function renderLegend(entityTypes) {
    const legend = document.getElementById('legend');
    legend.innerHTML = entityTypes.map(type => `
        <div class="legend-item">
            <div class="legend-color" style="background-color: ${ENTITY_COLORS[type] || '#e5e7eb'}"></div>
            <span class="legend-label">${type}</span>
        </div>
    `).join('');
}

/**
 * Handle entity extraction
 */
async function handleExtract() {
    const text = document.getElementById('input-text').value.trim();

    if (!text) {
        showError('Please enter some text');
        return;
    }

    showLoading(true);
    hideError();

    try {
        const response = await fetch(`${API_BASE}/extract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        if (!response.ok) throw new Error('Failed to extract entities');

        const result = await response.json();
        renderResults(result);
    } catch (error) {
        showError(error.message || 'An error occurred');
    } finally {
        showLoading(false);
    }
}

/**
 * Render extraction results
 */
function renderResults(result) {
    const { entities, stats } = result;

    if (entities.length === 0) {
        document.getElementById('no-results').classList.remove('hidden');
        document.getElementById('stats').classList.add('hidden');
        document.getElementById('entities-container').classList.add('hidden');
        return;
    }

    // Hide no-results message
    document.getElementById('no-results').classList.add('hidden');

    // Render stats
    document.getElementById('stat-total').textContent = stats.total_entities;
    document.getElementById('stat-high').textContent = stats.high_confidence;
    document.getElementById('stat-review').textContent = stats.needs_review;
    document.getElementById('stats').classList.remove('hidden');

    // Render entities
    const entitiesList = document.getElementById('entities-list');
    entitiesList.innerHTML = entities.map(entity => `
        <div class="entity-item ${entity.needs_review ? 'needs-review' : ''}">
            <span class="entity-label ${entity.label}" style="background-color: ${ENTITY_COLORS[entity.label] || '#e5e7eb'}">
                ${entity.label}
            </span>
            <span class="entity-text">${escapeHtml(entity.text)}</span>
            <div class="entity-confidence">
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${entity.confidence * 100}%"></div>
                </div>
                <span class="confidence-score">${(entity.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>
    `).join('');

    document.getElementById('entities-container').classList.remove('hidden');
}

/**
 * Show loading state
 */
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

/**
 * Show error message
 */
function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.classList.remove('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    document.getElementById('error').classList.add('hidden');
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
