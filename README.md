# Credit Spread Visualisation

Personal position-monitoring tool for credit spreads held in a moomoo account. Snapshots open spreads every 5 minutes during US market hours and renders mark-to-market PnL over time alongside the underlying price.

## Stack

- **Backend** — FastAPI · SQLAlchemy 2 · Alembic · APScheduler · `futu-api` (moomoo OpenD)
- **Frontend** — React 18 · TypeScript · Vite · Plotly.js · TanStack Query · Tailwind
- **Database** — PostgreSQL 16 (docker-compose)
- **Tooling** — `uv` (Python), `pnpm` (Node), `make` (orchestration)

## Quick start

Prerequisites: Docker, `uv`, `pnpm`, `jq`, and the **moomoo OpenD** desktop app running locally.

```bash
make setup     # creates .env, starts Postgres, installs deps, runs migrations
make dev       # runs API on :8000 and web on :5173
```

Then open <http://localhost:5173>.

To capture a snapshot immediately (otherwise the scheduler runs every 5 min during RTH):

```bash
make snapshot
```

## Layout

```
apps/api      FastAPI backend (uv-managed)
apps/web      React frontend (pnpm-managed)
docker-compose.yml
Makefile
```

## Make targets

Run `make help` for the full list.

## Status

v1 in progress. See [`docs/superpowers/specs/`](docs/superpowers/specs/) (when written) and the implementation plan for scope.
