# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Install development dependencies:

```bash
python -m pip install -e ".[test,dev]"
```

Run the full test suite:

```bash
pytest
```

Run one test:

```bash
pytest tests/unit/test_scoring.py::test_official_bpharm_item_scores_highly
```

Lint and type-check:

```bash
ruff check .
mypy app
```

Start the FastAPI web role locally:

```bash
uvicorn app.main:app --reload --port 8000
```

Start the worker role locally:

```bash
python -m app.scheduler.worker
```

Build the container:

```bash
docker build -t clex-pharma .
```

## Architecture

This is a Python 3.11+ all-India B.Pharm career-intelligence bot. `app/main.py` exposes the FastAPI web role and switches to the worker entry point when `PROCESS_ROLE=worker`. `app/api/` owns health and Telegram webhook boundaries; `app/bot/` owns Telegram API calls, update handling, and escaped message formatting; `app/db/` owns SQLAlchemy models, engine setup, and local schema initialization.

The discovery pipeline lives under `app/ingestion/`. Adapters return `DiscoveredItem` records and must not write directly to the database. `security.py` validates external URLs and identifies challenge pages; `http_client.py` applies response limits and raises a blocked-source error; `extraction/` parses page content and dates; `scoring.py`, `deduplication.py`, and `expiry.py` are pure business rules intended to stay independent of network and Telegram code. `app/scheduler/worker.py` is the long-running worker entry point.

`config/default_keywords.yaml`, `config/cities_states.yaml`, and `config/default_sources.yaml` hold nationwide source and search data. Geography must remain secondary to actual B.Pharm eligibility. Missing facts are represented as `Not specified / Not verified`; external content is escaped before Telegram output.

Production deployment uses PostgreSQL and separate Railway web/worker services from the same Docker image. Local development defaults to SQLite. `Dockerfile`, `docker-compose.yml`, `railway.toml`, `.env.example`, and `README.md` document the current deployment contract.

## Important constraints

Source collection must use only permitted public/API access. CAPTCHA, Cloudflare, authentication, robots, and anti-bot blocks are recorded and isolated; no bypass or challenge solving belongs in this repository. Keep external fetches bounded by URL safety, timeout, redirect, response-size, and per-source policies. Keep scoring deterministic and explainable so the bot never invents eligibility, deadlines, salary, or application links.

When adding an adapter, update its tests with fixed fixtures and preserve the normalized `DiscoveredItem` contract. When changing Telegram output, update formatting tests and continue escaping all external strings. When changing schema models, create or update an Alembic migration rather than relying only on startup table creation.
