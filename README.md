# SEO Crawler (Task1_Re5)

Terminal-driven website crawler built with **Crawlee** (Playwright) and **Python 3.10+**. It crawls a single domain, saves HTML locally, extracts SEO metadata, and stores results in **MongoDB**.

Designed for **Ubuntu 22.04** (also runs on other Linux/macOS with the same setup steps).

---

## Features

- Interactive terminal input: domain or full URL
- Same-domain crawl only (`www` treated as the same host; subdomains excluded)
- Crawl scope: **limited (default 50 pages)** or **whole site** (safety cap, default 10,000 pages)
- **Playwright** primary fetch with **HTTP (httpx)** fallback
- Per-page SEO fields: id, domain, URL, title, meta description, h1–h4, canonical, HTTP status, HTML path
- Local HTML + JSON sidecars under `html/{domain}/`
- MongoDB upsert per URL (re-crawls update existing records)
- Rotating log file: `logs/crawler.log`

---

## Prerequisites

1. **Python 3.10+** (`python3 --version`)
2. **MongoDB** running locally:

   ```bash
   # Example: ensure mongod is listening on default port
   mongosh --eval 'db.runCommand({ ping: 1 })'
   ```

3. System libraries for Playwright (Ubuntu):

   ```bash
   sudo apt-get update
   sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1
   ```

---

## Quick start

```bash
cd ~/Documents/projects/myproject/Task1_Re5

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium

bash run.sh
```

Or run the entry module directly:

```bash
source .venv/bin/activate
python terminal_main.py
```

### Interactive prompts

1. **Domain or URL** — e.g. `example.com` or `https://www.example.com`
2. **Crawl scope**
   - `1` — Limited (max **50** pages by default)
   - `2` — Whole site (all discoverable internal pages, capped at **10,000** by default)

---

## Output locations

All paths are relative to the project root unless overridden by environment variables.

| Output | Location |
|--------|----------|
| HTML files | `html/{domain}/page-1.html`, `page-2.html`, … |
| SEO JSON (per page) | `html/{domain}/page-1.json`, … |
| Crawl summary | `html/{domain}/summary.json` |
| Application logs | `logs/crawler.log` |
| Crawlee queue (internal) | `storage/` (auto-managed) |

### MongoDB

| Setting | Default |
|---------|---------|
| URI | `mongodb://localhost:27017` |
| Database | `seo_crawler` |
| Collection | `pages_{domain}` (e.g. `pages_example_com`) |

Example query:

```bash
mongosh seo_crawler --eval 'db.pages_example_com.find().limit(3).pretty()'
```

---

## Configuration

Edit `config.py` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PAGES` | `50` | Page limit for crawl scope option 1 |
| `MAX_PAGES_WHOLE_SITE` | `10000` | Safety cap for whole-site mode |
| `MAX_RETRIES` | `2` | Crawlee / handler retries |
| `MAX_CONCURRENCY` | `10` | Parallel browser requests |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `DB_NAME` | `seo_crawler` | Database name |
| `HTML_DIR` | `html` | Root folder for saved HTML |
| `LOG_DIR` | `logs` | Log directory |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG` for more detail) |
| `HEADLESS` | `true` | Playwright headless browser |
| `CRAWLEE_PURGE_ON_START` | `true` | Clear Crawlee local queue between runs |
| `IGNORE_HTTP_STATUS_CODES` | `404,410` | Treat these 4xx codes as non-fatal |

---

## Project structure

```
Task1_Re5/
├── terminal_main.py      # Entry point
├── run.sh                  # Setup venv + run crawler
├── config.py               # Settings
├── crawler.py              # Crawlee Playwright crawler + BFS
├── parser.py               # HTML → SEO fields
├── cli/
│   └── prompt.py           # Terminal input
├── models/
│   ├── schema.py           # Mongo field allowlist, indexes
│   └── seo_page.py         # SeoPageRecord model
├── db/
│   └── repository.py       # Mongo insert / query
├── storage/
│   └── file_storage.py     # HTML + JSON on disk
├── utils/                  # URL, security, logging, page id
├── tests/                  # Unit tests (parser, models)
├── html/                   # Created at runtime
├── logs/                   # Created at runtime
└── SCHEMA.md               # Detailed schema notes
```

---

## Extracted fields

Each crawled page is stored in MongoDB and in the matching `page-N.json` file:

| Field | Description |
|-------|-------------|
| `id` | Stable ID (UUID5 from normalized URL) |
| `domain` | Allowed host (e.g. `example.com`) |
| `url` | Page URL |
| `normalized_url` | Canonical URL form for deduplication |
| `page_name` | Last path segment |
| `title` | `<title>` |
| `meta_description` | Meta description or `og:description` |
| `canonical_url` | `<link rel="canonical">` if present |
| `h1`, `h2`, `h3`, `h4` | Heading text (lists) |
| `http_status_code` | HTTP status |
| `html_file_path` | Path to saved HTML file |
| `fetch_method` | `playwright` or `http_fallback` |
| `retry_count` | Retry count for the request |
| `created_at`, `updated_at` | Set on Mongo upsert |

---

## Tests

```bash
source .venv/bin/activate
pip install pytest   # optional, not in requirements.txt
pytest tests/ -q
```

---

## Troubleshooting

| Problem | What to check |
|---------|----------------|
| `Fatal: ... MongoDB` | Start MongoDB; verify `MONGO_URI` |
| `python: command not found` | Use `python3` and activate `.venv` |
| Playwright browser errors | Run `python -m playwright install chromium` |
| Many 404 errors in logs | Normal for broken links on the target site |
| Crawl stops at 50 pages | You chose limited mode; use option 2 for whole site |
| Empty `html/` folder | Crawl failed before saving; see `logs/crawler.log` |

---

## License

Sample / educational project — adjust as needed for your assignment or deployment.
