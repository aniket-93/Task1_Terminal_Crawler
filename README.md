# SEO Crawler (Task1_Re2)

Terminal-driven website crawler built with **Crawlee** (Playwright) and **Python 3.10+**. It crawls a single domain, saves HTML locally, extracts SEO metadata, and stores crawl/run stats and page records in **MongoDB**.

Designed for **Ubuntu 22.04** (also runs on other Linux/macOS with the same setup steps).

---

## Features

- Interactive terminal input: domain or full URL (no crawl-scope menu)
- Same-domain crawl only (`www` treated as the same host; other subdomains excluded)
- Up to **50 pages** per run by default (`MAX_PAGES_WHOLE_SITE`, configurable)
- **Playwright** primary fetch with **HTTP (httpx)** fallback
- SEO extraction: title, meta description, canonical, h1–h4, HTTP status
- **`page_name`** = document `<title>` (URL slug only if title is missing)
- Local HTML + JSON sidecars under `html/{domain}/` (URL-based filenames)
- MongoDB: **`domains`** (one row per domain name) and **`pages`** (linked by `domain_id`)
- Upsert on re-crawl: same domain / same URL updates existing Mongo documents
- Crawl timing stored on domain as **`total_crawl_time`** (seconds)
- Rotating log file: `logs/crawler.log`

---

## Prerequisites

1. **Python 3.10+** (`python3 --version`)
2. **MongoDB** running locally:

   ```bash
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
cd ~/Documents/projects/myproject/Task1_Re2

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

### Interactive prompt

- **Domain or URL** — e.g. `example.com` or `https://www.example.com`

The crawler starts immediately with the configured page limit (default 50).

---

## Output locations

All paths are relative to the project root unless overridden by environment variables.

| Output | Location |
|--------|----------|
| HTML files | `html/{domain}/index.html`, `catalogue_book-title_index.html`, … |
| SEO JSON (per page) | `html/{domain}/{same-stem}.json` |
| Crawl summary | `html/{domain}/summary.json` |
| Application logs | `logs/crawler.log` |
| Crawlee queue (internal) | `storage/` (auto-managed; purged between runs by default) |

### HTML file naming

Paths are derived from the URL path, not sequential `page-1`, `page-2`:

| URL path | File |
|----------|------|
| `/` | `index.html` |
| `/social-media` | `social-media_index.html` |
| `/catalogue/book_20/index.html` | `catalogue_book_20_index.html` |

`html_file_path` in MongoDB matches this layout (e.g. `html/example.com/social-media_index.html`).

---

## MongoDB

| Setting | Default |
|---------|---------|
| URI | `mongodb://localhost:27017` |
| Database | `seo_crawler` |
| Collections | `domains`, `pages` |

### `domains` (one document per `domain_name`)

| Field | Description |
|-------|-------------|
| `domain_name` | Allowed host (unique) |
| `status` | `running` during crawl; then `completed` or `failed` |
| `total_pages` | Max pages limit for this run |
| `crawled_pages` | Pages successfully saved this run |
| `failed_pages` | URLs that failed after retries this run |
| `start_url` | Seed URL |
| `total_crawl_time` | Wall-clock seconds for the last run (2 decimal places) |
| `created_at`, `updated_at`, `last_crawled_at` | ISO UTC timestamps |

### `pages` (one document per URL per domain)

Keyed by **`(domain_id, url)`**. Linked to `domains` via **`domain_id`** (ObjectId).

| Field | Description |
|-------|-------------|
| `domain_id` | References `domains._id` |
| `domain` | Allowed host |
| `url`, `normalized_url` | Page URL |
| `page_name` | Document `<title>` (fallback: URL slug) |
| `title`, `meta_description`, `canonical_url` | SEO meta |
| `h1`, `h2`, `h3`, `h4` | Heading text (arrays) |
| `http_status_code` | HTTP status |
| `html_file_path` | Relative path to saved HTML |
| `fetch_method` | `playwright` or `http_fallback` |
| `retry_count` | Request retry count |
| `error` | Failure reason (failed URLs only; otherwise `null`) |
| `is_duplicate` | `false` on crawled pages (reserved for future use) |
| `created_at`, `updated_at` | Set on upsert; `created_at` preserved on update |

Duplicate URLs discovered during link discovery are **not** written to `pages` (tracked in logs and `summary.json` only).

### Example queries

```bash
mongosh seo_crawler --eval 'db.domains.find().pretty()'
mongosh seo_crawler --eval 'db.pages.find({domain:"books.toscrape.com"}).limit(3).pretty()'
```

### Re-running the same domain

| Collection | Behavior |
|------------|----------|
| `domains` | Same `_id`; counters and `status` reset at start, updated at end; `created_at` kept |
| `pages` | Same URL → **update** existing row (`updated_at`, SEO fields refreshed); new URLs → insert |
| Leftover pages | URLs not crawled in the new run **remain** unchanged in Mongo |
| Disk HTML | Same URL path → file **overwritten** when that URL is crawled again |

See **`SCHEMA.md`** for full schema and indexing notes.

---

## Configuration

Edit `config.py` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PAGES` | `50` | Optional manual cap if you pass `max_pages` in code |
| `MAX_PAGES_WHOLE_SITE` | `50` | Default terminal crawl limit |
| `MAX_RETRIES` | `2` | Crawlee / handler retries |
| `MAX_CONCURRENCY` | `10` | Parallel browser requests |
| `REQUEST_DELAY_MS` | `300` | Delay between requests |
| `REQUEST_TIMEOUT_SEC` | `30` | Request timeout |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `DB_NAME` | `seo_crawler` | Database name |
| `HTML_DIR` | `html` | Root folder for saved HTML |
| `LOG_DIR` | `logs` | Log directory |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG` for duplicate URL traces) |
| `HEADLESS` | `true` | Playwright headless browser |
| `CRAWLEE_PURGE_ON_START` | `true` | Clear Crawlee local queue between runs |
| `IGNORE_HTTP_STATUS_CODES` | `404,410` | Treat these 4xx codes as non-fatal |

---

## Project structure

```
Task1_Re2/
├── terminal_main.py      # Entry point
├── run.sh                # venv + deps + run crawler
├── config.py             # Settings (env overrides)
├── crawler.py            # Crawlee Playwright crawler + BFS
├── parser.py             # HTML → SEO fields
├── cli/
│   └── prompt.py         # Terminal domain/URL input
├── models/
│   ├── schema.py         # Mongo collections, fields, indexes
│   └── seo_page.py       # SeoPageRecord model
├── db/
│   └── repository.py     # domains / pages CRUD
├── storage/
│   ├── file_storage.py   # HTML + JSON on disk
│   └── mongodb.py        # Re-exports (compat)
├── utils/                # URL, security, logging, link policy
├── tests/                # Unit tests (parser, models, file paths)
├── html/                 # Created at runtime
├── logs/                 # Created at runtime
├── storage/              # Crawlee internal (runtime)
└── SCHEMA.md             # Detailed schema and assumptions
```

---

## Tests

```bash
source .venv/bin/activate
python -m unittest tests.test_parser tests.test_seo_page_model tests.test_file_storage -v
```

Optional: `pip install pytest` then `pytest tests/ -q`.

---

## Troubleshooting

| Problem | What to check |
|---------|----------------|
| `Fatal: ... MongoDB` | Start MongoDB; verify `MONGO_URI` |
| `python: command not found` | Use `python3` and activate `.venv` |
| Playwright browser errors | Run `python -m playwright install chromium` |
| Many 404 errors in logs | Normal for broken links; 404/410 are ignored as crawl failures |
| Crawl stops at 50 pages | Default limit; raise `MAX_PAGES_WHOLE_SITE` |
| Empty `html/` folder | Crawl failed before saving; see `logs/crawler.log` |
| Old stub `pages` with `is_duplicate: true` | From an earlier version; delete with `db.pages.deleteMany({is_duplicate: true})` and re-crawl |

---

## License

Sample / educational project — adjust as needed for your assignment or deployment.
