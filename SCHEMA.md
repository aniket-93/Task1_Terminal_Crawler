# Assumptions (documented defaults)

| Topic | Rule |
|-------|------|
| Input | `example.com` → `https://example.com/` |
| Same domain | Host must match seed host exactly after stripping `www.`; other subdomains excluded |
| Max pages | Default **50** (`MAX_PAGES` / `MAX_PAGES_WHOLE_SITE`). Override with env vars. |
| Crawler | `PlaywrightCrawler` primary; one `httpx` attempt on Playwright failure |
| Retries | Crawlee `max_request_retries=2`; retry 5xx/429/timeouts, not 404 |
| Visited | Added after successful save or final failure |
| Duplicates | URL in `visited` or `enqueued` — logged in summary only; **not** written to `pages` |
| MongoDB | Database `seo_crawler`; collections **`domains`** and **`pages`** |
| HTML | `html/{domain}/{path-slug}_index.html` (e.g. `social-media_index.html`; root = `index.html`) |

# Project layout (modules)

| Module | Role |
|--------|------|
| `cli/prompt.py` | Terminal input (domain) |
| `crawler.py` | Crawlee crawler logic |
| `parser.py` | HTML metadata parsing |
| `storage/file_storage.py` | HTML/JSON file storage |
| `models/schema.py` | Mongo field allowlists, collection names, indexes |
| `models/seo_page.py` | `SeoPageRecord` document model |
| `db/repository.py` | Mongo domains/pages CRUD |
| `config.py` | Configuration (env overrides) |
| `terminal_main.py` | Terminal entry point |

# MongoDB schema

**Database:** `seo_crawler`

## `domains`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `domain_name` | string | unique |
| `status` | string | `queued` \| `running` \| `completed` \| `failed` |
| `total_pages` | int | max pages for this run |
| `crawled_pages` | int | successful saves |
| `failed_pages` | int | URLs that failed after retries |
| `start_url` | string | seed URL |
| `created_at` | ISO UTC string | |
| `updated_at` | ISO UTC string | |
| `last_crawled_at` | ISO UTC string | |
| `total_crawl_time` | number | wall-clock seconds for the last run (2 decimal places) |

## `pages`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `domain_id` | ObjectId | FK → `domains._id` |
| `domain` | string | allowed host |
| `url` | string | unique per `domain_id` |
| `normalized_url` | string | |
| `page_name` | string | document `<title>` (fallback: URL slug) |
| `title` | string \| null | |
| `meta_description` | string \| null | |
| `canonical_url` | string \| null | |
| `h1`, `h2`, `h3`, `h4` | array[string] | |
| `http_status_code` | int | |
| `html_file_path` | string | |
| `fetch_method` | string | |
| `retry_count` | int | |
| `error` | string \| null | failure reason |
| `is_duplicate` | bool | true when URL skipped as duplicate |
| `created_at` | ISO UTC string | |
| `updated_at` | ISO UTC string | |

**Indexes:** `domains.domain_name` (unique); `pages.(domain_id, url)` (unique); `pages.domain_id`.

# Folder structure

```
html/
  example.com/
    index.html
    social-media_index.html
    social-media_index.json
    summary.json
logs/
  crawler.log
storage/          # Crawlee internal queue (auto)
```

# Run

```bash
cd ~/Documents/projects/myproject/Task1_Re2
source .venv/bin/activate
bash run.sh
```

# Query examples

```bash
mongosh seo_crawler --eval 'db.domains.find().pretty()'
mongosh seo_crawler --eval 'db.pages.find({domain:"example.com"}).limit(3).pretty()'
```
