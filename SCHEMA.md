# Assumptions (documented defaults)

| Topic | Rule |
|-------|------|
| Input | `example.com` → `https://example.com/` |
| Same domain | Host must match seed host exactly after stripping `www.`; other subdomains excluded |
| Max pages | **Limited:** default 50 (`MAX_PAGES`). **Whole site:** up to `MAX_PAGES_WHOLE_SITE` (default 10000). Terminal prompts 1 or 2. |
| Crawler | `PlaywrightCrawler` primary; one `httpx` attempt on Playwright failure |
| Retries | Crawlee `max_request_retries=2`; retry 5xx/429/timeouts, not 404 |
| Visited | Added after successful save or final failure |
| Duplicates | URL in `visited` or `enqueued` — logged, not re-crawled |
| MongoDB | Database `seo_crawler`; **collection per domain** `pages_{host}`; re-run upserts by `url` |
| HTML | `html/{domain}/page-{n}.html` (1-based, resets each run) |

# Project layout (modules)

| Module | Role |
|--------|------|
| `cli/prompt.py` | Terminal input (domain, crawl scope) |
| `crawler.py` | Crawlee crawler logic |
| `parser.py` | HTML metadata parsing |
| `storage/file_storage.py` | HTML/JSON file storage |
| `models/schema.py` | Mongo field allowlist, collection naming, indexes |
| `models/seo_page.py` | `SeoPageRecord` document model |
| `db/repository.py` | Mongo insert/query (`save_page`, `find_page_by_url`, `ping`) |
| `config.py` | Configuration (env overrides) |
| `terminal_main.py` | Terminal entry point |

# MongoDB schema

**Database:** `seo_crawler`  
**Collection per domain:** `pages_example_com`, `pages_yahoo_com`, …

Defined in `models/schema.py` and `models/seo_page.py`.

| Field | Type |
|-------|------|
| id | string (stable UUID5 from `normalized_url`) |
| domain | string (allowed host, e.g. `example.com`) |
| url | string (unique per collection) |
| normalized_url | string |
| page_name | string |
| title | string \| null |
| meta_description | string \| null |
| canonical_url | string \| null |
| h1, h2, h3, h4 | array[string] |
| http_status_code | int |
| html_file_path | string |
| fetch_method | string |
| retry_count | int |
| created_at | ISO UTC string |
| updated_at | ISO UTC string |

# Folder structure

```
html/
  example.com/
    page-1.html
    page-1.json
    page-2.html
    ...
    summary.json
logs/
  crawler.log
storage/          # Crawlee internal queue (auto)
```

# Run

```bash
cd ~/Documents/projects/myproject/Task1_Re5
source .venv/bin/activate
bash run.sh
```
