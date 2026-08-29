# CLEX Pharma

CLEX Pharma is an all-India B.Pharm career-intelligence Telegram bot. It is designed to discover internships, jobs, government vacancies, exams, notices, research opportunities, and deadlines; verify source quality; classify B.Pharm fit; score and deduplicate items; and deliver concise alerts.

## Architecture

The application is a Python service with two runtime roles. The web role is a FastAPI application exposing `/health`, `/health/live`, `/health/ready`, and `/telegram/webhook`. The worker role runs the scheduled ingestion process. PostgreSQL is the production persistence layer; SQLite is supported for local development. Source adapters return normalized discovery records, and pure scoring, expiry, fingerprint, extraction, and security functions keep core behavior testable without Telegram or live websites.

The initial adapters support RSS-style discovery and configured public HTML pages. Public social sources must be integrated only through legitimate APIs or permitted public/indexed access. CAPTCHA, Cloudflare, login walls, robots restrictions, and anti-bot challenges are recorded as blocked source events; the bot never attempts to bypass them. JavaScript-only pages may produce no discoveries because the worker does not execute browser scripts.

The worker runs an ingestion cycle immediately on startup and then every `CRAWL_INTERVAL_SECONDS` (default two hours). Each cycle seeds the configured sources, filters relevant same-host links, and persists scored, non-expired opportunities. A failed source is isolated and recorded in `source_runs`; repeated cycles refresh records instead of creating duplicates.


## Local setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -e ".[test,dev]"
copy .env.example .env
pytest
```

Run the web service locally:

```bash
uvicorn app.main:app --reload --port 8000
```

Run the worker locally:

```bash
python -m app.scheduler.worker
```

Run one test:

```bash
pytest tests/unit/test_scoring.py::test_official_bpharm_item_scores_highly
```

Run linting and type checks:

```bash
ruff check .
mypy app
```

## Configuration

Copy `.env.example` to `.env`. Required production values are `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `PUBLIC_BASE_URL`, and `ADMIN_TELEGRAM_IDS`. `PROCESS_ROLE` is `web` or `worker`. `TELEGRAM_CHAT_ID` is optional for local testing and should be populated through `/start` in normal use. Do not place credentials in source control.

Nationwide keywords, states, union territories, cities, hubs, and official seed sources live in `config/`. These files are data inputs and can be expanded without changing the scoring code. Geography is secondary to actual B.Pharm eligibility.

## Docker and Railway

Build and run the web role:

```bash
docker build -t clex-pharma .
docker run --env-file .env -e PROCESS_ROLE=web -p 8000:8000 clex-pharma
```

`docker-compose.yml` provides local PostgreSQL plus separate web and worker containers. Railway should provision one PostgreSQL service and create web and worker services from the same Dockerfile. Set `PROCESS_ROLE=web` on the web service and use `python -m app.scheduler.worker` as the worker command. The Railway health check is `/health/live`.

The current repository supports schema creation at startup for local operation. Alembic files are included for the production migration workflow; run the migration command against the Railway database before enabling ingestion in a production environment.

## Telegram behavior

Supported user commands include `/start`, `/help`, `/status`, `/latest`, `/internships`, `/jobs`, `/govt`, `/exams`, `/notices`, `/deadlines`, `/search`, `/sources`, `/settings`, `/pause`, and `/resume`. Admin authorization is based on numeric Telegram IDs in `ADMIN_TELEGRAM_IDS`. Messages escape external HTML and show `Not specified / Not verified` for missing fields. Community and discovery-only results are never labeled official.

## Data quality and security

Every item has a fit classification, trust level, score reasons, and expiry state. Explicit B.Pharm eligibility outranks geographic relevance. URLs are checked for HTTP(S), DNS resolution, private/reserved network targets, and challenge pages before fetching. HTTP responses are bounded by size, timeout, redirect, and status policies. External text is treated as untrusted content and is escaped before Telegram delivery.

This initial release does not solve CAPTCHAs, scrape private/authenticated portals, bypass rate limits, download copyrighted videos, or infer missing salary, deadline, eligibility, or application data. Live source coverage and OCR for scanned PDFs are extension points that require separate permitted adapters and fixtures.

## Tests

The unit suite covers B.Pharm fit classification, explainable score calculation, deadline bands, stable fingerprints, blocked-source detection, SSRF safeguards, and Telegram formatting. Add integration fixtures for PostgreSQL and mocked Telegram delivery as the database-backed repository and full notification pipeline are expanded.
