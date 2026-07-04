# DeFi Agent

A **read-only** DeFi query & analysis agent. Ask about a wallet or a transaction in natural language and get
structured answers — cross-chain transfer status, Morpho lending positions, transaction decoding, balances — as
rich UI cards. No private keys, no signing, no sending: every tool is read-only.

- **Chains:** Ethereum · BNB Smart Chain · Arbitrum · Base · Optimism
- **Protocols:** [LI.FI](https://li.fi) (cross-chain status) · [Morpho](https://morpho.org) (lending positions/markets)
- **Explorer:** pure-RPC transaction lookups (get / decode / logs / ENS / native balance)

## How it works

A **hybrid LangGraph** design: deterministic nodes for the guardrails (scope guard, intent classification, entity
extraction, refusal, human-in-the-loop clarification) plus tool-calling agents for the two protocol lines.

```
                       ┌─ wallet line ─→ extract address/ENS ─→ wallet_agent ─→ [Morpho positions, balance]
user ─→ guard_scope ─→ classify_intent ┤
                       └─ tx line ──────→ extract tx hash ────→ tx_agent ─────→ [Explorer, LI.FI status, Morpho]
                       └─ out of scope ─→ refuse
```

- **Scope guard** (structured output) refuses anything outside wallets/transactions or the supported chains/protocols.
- **Missing input** (no address/hash) triggers an `interrupt()` that asks the user, then resumes.
- **Cards from tool artifacts:** tools return a human string for the LLM *and* a structured artifact; the API emits a
  `card` SSE event so the frontend renders a `LifiStatusCard` / `MorphoPositionsCard`.
- **Prompt caching:** system prompt + tools are cached via `cache_control` for cheaper/faster calls.

## Stack

- **Backend:** Python 3.11 · [uv](https://docs.astral.sh/uv/) · LangGraph + `langchain-anthropic`
  (Haiku for routing/guard, Sonnet for analysis) · FastAPI + SSE · web3 · httpx
- **Storage:** PostgreSQL — LangGraph Postgres checkpointer (durable conversations + interrupt resume) and business
  tables (`users` / `api_keys` / `threads`) via SQLAlchemy + Alembic
- **Frontend:** Next.js (App Router) + React — vendored card UI in `web/chat-ui/`, consumes the SSE stream
- **Observability:** LangSmith tracing · structured JSON logs · `audit_log` table · routing eval

## Quickstart

Prerequisites: `uv`, Node 22+, Docker.

```bash
# 1. Local Postgres (trust auth, bound to 127.0.0.1)
docker compose up -d

# 2. Environment — copy and fill in ANTHROPIC_API_KEY (RPC endpoints default to public nodes)
cp .env.example .env
#   DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/defi_agent
#   LANGGRAPH_PG_DSN=postgresql://postgres@localhost:5432/defi_agent

# 3. Business-table migrations
uv run alembic upgrade head
```

### Run it

```bash
# Terminal CLI (multi-turn chat; interrupt & resume)
uv run python scripts/chat.py

# API (SSE) on :8000
uv run uvicorn app.main:app --port 8000

# Frontend on :3000  (needs the API running)
cd web && npm install && npm run dev

# LangGraph Studio (visualize the graph)
uv run langgraph dev
```

Connect a wallet in the web UI (SIWE — a gas-free signature) and "my positions / my balance" queries auto-resolve to
your address. Everything stays read-only.

## API

| Endpoint | Purpose |
|---|---|
| `POST /v1/chat` | Chat (SSE: `start` / `token` / `tool_call` / `tool_result` / `card` / `interrupt` / `done`) |
| `POST /v1/chat/resume` | Resume after an `interrupt` |
| `GET /v1/threads/{id}/history` | Thread message history (owner-scoped) |
| `POST /v1/auth/nonce` · `POST /v1/auth/verify` | SIWE sign-in → JWT |
| `GET /healthz` · `GET /readyz` | Health / readiness |

Auth is three-way: anonymous session token · SIWE JWT · widget API key.

## Testing

```bash
uv run pytest                      # unit tests (tools mocked via respx / fake web3)
uv run python scripts/eval_routing.py   # scope-guard routing accuracy
uv run ruff check app/ scripts/ tests/  # lint
```

Verified real-data fixtures (Ethereum mainnet):

- **tx** `0x7459…a1abd` — LI.FI cross-chain swap+bridge (USDT → BNB via Squid), status `DONE`
- **wallet** `0x7b52…8748` — Morpho borrow position (RLUSD against cbBTC)

## Layout

```
app/
  main.py            # FastAPI app (lifespan, SSE, auth, identity)
  config.py          # settings (models, endpoints)
  agent/             # graph.py, state.py, prompts.py, checkpointer.py, tools/
  api/               # identity (three-way auth), SIWE auth
  chains/            # chain registry (5 chains) + web3 clients
  storage/           # SQLAlchemy models, engine, repo
  observability/     # structured logging, audit_log
scripts/             # chat.py (CLI), eval_routing.py
migrations/          # Alembic
tests/               # pytest
web/                 # Next.js frontend (chat-ui card library + DefiChat host)
```

> This is a read-only tool for querying public on-chain data. It never holds keys, signs, or moves funds, and it does
> not provide financial advice.
