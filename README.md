# DeFi Agent

A **read-only** DeFi query & analysis agent. Ask about a wallet or a transaction in natural language and get
structured answers — cross-chain transfer status, Morpho lending positions, transaction decoding, balances — as
rich UI cards, or ask a conceptual question ("how does Morpho liquidation work?") and get a doc-grounded answer with
cited sources. No private keys, no signing, no sending: every tool is read-only.

- **Chains:** Ethereum · BNB Smart Chain · Arbitrum · Base · Optimism
- **Protocols:** [LI.FI](https://li.fi) (cross-chain status) · [Morpho](https://morpho.org) (lending positions/markets)
- **Explorer:** pure-RPC transaction lookups (get / decode / logs / ENS / native balance)
- **Docs (RAG):** conceptual Q&A grounded in the LI.FI & Morpho documentation, with cited sources

## How it works

A **hybrid LangGraph** design: deterministic nodes for the guardrails (scope guard, intent classification, entity
extraction, refusal, human-in-the-loop clarification) plus tool-calling agents for the two protocol lines.

```
                       ┌─ wallet line ────→ extract address/ENS ─→ wallet_agent ─→ [Morpho positions, balance]
user ─→ guard_scope ─→ ┤ tx line ─────────→ extract tx hash ────→ tx_agent ─────→ [Explorer, LI.FI status, Morpho]
     (intent+protocol) ┤ knowledge line ──→ retrieve_docs ───────→ knowledge_answer → [grounded answer + sources]
                       └─ out of scope ───→ refuse
```

- **Scope guard** (structured output) classifies intent (wallet / transaction / knowledge) and, for concept
  questions, the protocol; it refuses anything outside the supported scope, chains, or protocols.
- **Knowledge line (RAG):** conceptual questions (no address/hash) retrieve protocol-scoped chunks from a pgvector
  store (cosine top-k=5) and answer **only** from them, citing sources and saying so when the docs don't cover it.
  Retrieved text is passed as data (never as instructions) and the answer streams token-by-token like the other lines.
- **Missing input** (no address/hash) triggers an `interrupt()` that asks the user, then resumes.
- **Cards from tool artifacts:** tools return a human string for the LLM *and* a structured artifact; the API emits a
  `card` SSE event so the frontend renders a `LifiStatusCard` / `MorphoPositionsCard`.
- **Prompt caching:** static prompt text comes first so DeepSeek's automatic context (prefix) caching hits;
  dynamic content (resolved address/hash, retrieved docs) follows.

## Stack

- **Backend:** Python 3.11 · [uv](https://docs.astral.sh/uv/) · LangGraph + `langchain-deepseek`
  (deepseek-v4-flash for routing/guard, deepseek-v4-pro for analysis) · FastAPI + SSE · web3 · httpx
- **Storage:** PostgreSQL — LangGraph Postgres checkpointer (durable conversations + interrupt resume), business
  tables (`users` / `api_keys` / `threads`), and a `doc_chunks` **pgvector** table (HNSW cosine index) via
  SQLAlchemy + Alembic
- **RAG:** on-device embeddings ([`bge-small`](https://huggingface.co/BAAI/bge-small-en-v1.5), 384-dim, via
  `sentence-transformers`) — no embedding API calls; docs ingested from the LI.FI & Morpho sites as markdown
- **Frontend:** Next.js (App Router) + React — vendored card UI in `web/chat-ui/`, consumes the SSE stream
- **Observability:** LangSmith tracing · structured JSON logs · `audit_log` table · routing eval

## Quickstart

Prerequisites: `uv`, Node 22+, Docker.

```bash
# 1. Local Postgres with pgvector (trust auth, bound to 127.0.0.1)
docker compose up -d

# 2. Environment — copy and fill in DEEPSEEK_API_KEY (RPC endpoints default to public nodes)
cp .env.example .env
#   DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/defi_agent
#   LANGGRAPH_PG_DSN=postgresql://postgres@localhost:5432/defi_agent

# 3. Migrations — business tables + the pgvector doc_chunks store
uv run alembic upgrade head

# 4. Ingest the LI.FI & Morpho docs into pgvector (downloads bge-small on first run; re-runnable/idempotent)
uv run python scripts/ingest_docs.py
```

> **pgvector requirement:** the knowledge line needs the `vector` extension. The bundled
> `pgvector/pgvector:pg16` image ships it, and the migration runs `CREATE EXTENSION IF NOT EXISTS vector`
> (needs a superuser the first time — the default `postgres` role qualifies; on managed Postgres, enable the
> pgvector extension for the database first).

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
uv run python scripts/eval_routing.py   # scope-guard routing accuracy (wallet / tx / knowledge / refuse)
uv run ruff check app/ scripts/ tests/  # lint
```

Retrieval tests skip automatically when the pgvector `doc_chunks` table isn't reachable; the real-model guard
classification test skips without `DEEPSEEK_API_KEY`. The routing eval covers the knowledge intent alongside
wallet / transaction / refuse.

Verified real-data fixtures (Ethereum mainnet):

- **tx** `0x7459…a1abd` — LI.FI cross-chain swap+bridge (USDT → BNB via Squid), status `DONE`
- **wallet** `0x7b52…8748` — Morpho borrow position (RLUSD against cbBTC)

## Layout

```
app/
  main.py            # FastAPI app (lifespan, SSE, auth, identity, embedder warmup)
  config.py          # settings (models, endpoints)
  agent/             # graph.py, state.py, prompts.py, checkpointer.py, tools/
    knowledge/       # RAG: embed.py (bge-small), store.py (pgvector search), ingest.py (chunking)
  api/               # identity (three-way auth), SIWE auth
  chains/            # chain registry (5 chains) + web3 clients
  storage/           # SQLAlchemy models (incl. doc_chunks), engine, repo
  observability/     # structured logging, audit_log
scripts/             # chat.py (CLI), eval_routing.py, ingest_docs.py (doc ingestion)
migrations/          # Alembic
tests/               # pytest
web/                 # Next.js frontend (chat-ui card library + DefiChat host)
```

> This is a read-only tool for querying public on-chain data. It never holds keys, signs, or moves funds, and it does
> not provide financial advice.
