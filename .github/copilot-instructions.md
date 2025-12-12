# Datathon: AI Coding Agent Instructions

## Project Overview
**BCL Regulatory Watch** is an automated document surveillance system for the Banque Centrale du Luxembourg. It scrapes regulatory PDFs from `bcl.lu`, extracts and translates content (via Groq LLM), then analyzes for keyword matches against a regulatory keyword list.

**Key Users:** Financial/compliance analysts in Luxembourg targeting French, German, or English content.

## Architecture & Data Flow

### Pipeline Stages (see `orchestration.py`)
The system follows a strict 5-stage pipeline that processes each document sequentially:

1. **Scraping** (`ScraperAgent`) → Downloads PDFs from BCL website
2. **Extraction** (`ExtractionAgent`) → Extracts text from PDFs (max 5 pages for demo)
3. **Translation** (`TranslationAgent`) → Uses Groq Llama 3.1 70B to translate preview (3000 chars) to target language
4. **Analysis** (`AnalyzerAgent`) → Keyword matching against `Key Words.csv`
5. **Notification** (`NotificationAgent`) → Email alert if matches found (score > 0)

**Critical:** Agents are decoupled—translator must NOT import `orchestration.py` (see translator.py note). Pipeline orchestrates flow sequentially; no parallelization currently.

### Key Data Structures
- `SOURCES_CONFIG` (config.py): Array defining crawl targets (BCL only currently)
  - `type: "bcl_web_scraping"` dispatches to `_crawl_bcl_site()`
  - `limit: 20` caps PDFs per demo run to avoid overwhelming downloads
- `KEYWORDS_FILE` ("Key Words.csv"): Simple list of regulatory keywords (one per line or cell)
- Pipeline output: `DataFrame` with columns: `source`, `file`, `path`, `date`, `score`, `matches`, `preview`

### Storage: Data Lake (no deletion)
- Downloaded PDFs persist in `data_lake_bcl/` (not auto-deleted)
- Extracted JSON/CSV results stored in `data/` folder
- Design assumes filesystem for demos; scalable to cloud storage

## Critical Developer Workflows

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (required for translation)
set GROQ_API_KEY=your_groq_api_key
# Optional: set EMAIL_USER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

# Run Streamlit UI
streamlit run main_app.py
```

### Development Testing
- `test_api.py`: Test API endpoints (status unclear—check for active tests)
- No automated test suite currently; testing is manual via Streamlit UI
- For debugging agents: inject `logger.info()` calls (utils/logger.py) and check console output

### Key Configuration Points
- Modify `SOURCES_CONFIG` in `config.py` to add new source types (e.g., other central bank websites)
- Edit `Key Words.csv` to change detection keywords
- `ALERT_THRESHOLD` (config.py, currently 1) controls which documents trigger alerts

## Project-Specific Patterns & Conventions

### Agent Architecture Pattern
All agents follow a consistent structure:
- Single class per agent (e.g., `class ScraperAgent`, `class TranslationAgent`)
- Logger initialized via `setup_logger()` from utils
- Errors logged, not raised (graceful degradation):
  - Missing API key → warns user, returns placeholder text
  - Missing PDF → returns empty string, logs error
  - Malformed CSV → uses hardcoded fallback keywords

**Example:** See `translator.py` for safe API failure handling; `analyzer.py` for CSV parsing robustness.

### BCL-Specific Scraping Logic
`ScraperAgent._crawl_bcl_site()` uses a 2-tier approach:
1. Fetch main page, extract subsection links (filter by `/reporting_reglementaire/` path)
2. Visit each subsection, extract PDF links
3. Download PDFs sequentially with browser headers to avoid being blocked

**Important:** Links are relative on BCL site—use `urljoin()` (urllib.parse) for proper URL construction.

### Text Extraction Limitations
- `ExtractionAgent` uses `pypdf.PdfReader` (simple extraction, no OCR)
- Scanned PDFs (image-based) return placeholder: `"[PDF Image - OCR non activé...]"`
- Only reads first 5 pages per PDF for performance (demo mode)
- For production: consider adding OCR (Tesseract) or cloud APIs

### Internationalization (i18n)
- UI strings are French + variable English (country_map in main_app.py)
- Translation API prompt hardcoded in `TranslationAgent.translate()`: update here for language support changes
- Preview returned as translated text; full document stored as-is for audit trails

### Keyword Analysis Strategy
- Case-insensitive substring matching (`text_lower`, `k in text_lower`)
- No stemming/lemmatization currently (simple but may miss variants like "energy"/"energetic")
- Returns all matched keywords as a deduplicated list
- If keyword file missing, falls back to hardcoded list (NREL-context terms: "energy", "compliance", etc.)

## Integration Points & External Dependencies

### APIs & External Services
| Service | Config | Purpose | Failure Mode |
|---------|--------|---------|--------------|
| **Groq (Llama 3.1 70B)** | `GROQ_API_KEY` env var | Translation | Falls back to untranslated text |
| **Gmail SMTP** | `EMAIL_*` env vars | Alerts | Logs warning, silently skips |
| **BCL Website** | `https://www.bcl.lu/...` | PDF source | Logs error, continues to next page |

### Dependencies
- **streamlit**: UI framework (main_app.py)
- **pandas**: Data manipulation (results DataFrame)
- **beautifulsoup4 + requests**: HTML scraping (ScraperAgent)
- **pypdf**: PDF text extraction (ExtractionAgent)
- **groq**: LLM API client (TranslationAgent)
- **python-dotenv**: Environment variable loading
- **torch, transformers**: Installed but currently unused (potential future use for local NLP)

## Common Pitfalls & Gotchas

1. **Missing env vars silently degrade features** — translator and notifier don't fail loudly; check logs
2. **PDF download limit in config** — `limit: 20` is intentionally low for demo; remove or increase for production
3. **Text extraction is max 5 pages** — scanned documents won't extract properly (no OCR)
4. **Keyword CSV parsing is fragile** — different delimiters may fail; pandas engine='python' handles flexibility
5. **No caching** — full pipeline re-runs on every "LANCER" button click; optimize translation step for repeated runs
6. **SSRF validation** — `SecurityManager.validate_url()` enforces domain whitelist; BCL only currently

## Code Quality Standards
- **No type hints** (current codebase); if adding new agents, follow existing pattern (optional typing)
- **Logging as primary debug tool** — use `logger.info()`, `logger.error()` instead of print()
- **Graceful degradation** — expect API failures, network timeouts; don't crash the pipeline
- **Streamlit session state** — `st.session_state['results']` persists DataFrame across UI interactions; clear with `st.button()` callbacks if needed

## File Structure Reference
```
main_app.py          # Streamlit UI (2 tabs: BCL Analysis, PDF Data Lake)
orchestration.py     # Pipeline orchestrator (5-stage flow)
config.py            # Centralized configuration
agents/
  scraper.py         # Web crawling + PDF download
  extractor.py       # PDF → text conversion
  translator.py      # Groq API translation
  analyzer.py        # Keyword matching
  notifier.py        # Email alerts
utils/
  logger.py          # Logging setup
  security.py        # SSRF/path traversal validation
data_lake_bcl/       # Downloaded PDF storage
data/                # Output CSV/JSON results
Key Words.csv        # Keyword list for detection
```

---
**Last Updated:** December 2025 | Focus: Regulatory document surveillance system for central banking compliance
