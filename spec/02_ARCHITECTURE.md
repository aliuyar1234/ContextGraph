# Architecture — OCG (Open Context Graph)

## Architecture summary
OCG is a self-hosted system with:
- A single API service (FastAPI) exposing REST + serving the UI.
- Background worker pools for ingestion and graph processing.
- A Postgres system-of-record for entities, traces, permissions, and derived models.
- A Redis-backed job queue for asynchronous work.
- Optional pgvector usage for similarity/embeddings (feature-flagged).
- Optional object storage only when raw attachments are enabled (OFF by default).

## Component boundary table (normative)

| Component | Responsibility | Owns state? | Dependencies | Public surface |
|---|---|---:|---|---|
| Web UI (Next.js) | Admin + analytics + personal dashboards | No | API service | HTTP (browser) |
| API Service (FastAPI) | AuthN/Z, REST API, query composition, permission filtering | No (stateless) | Postgres, Redis, OIDC | REST `/api/v1/*`, `/healthz` |
| Connector Runner (Workers) | Pull/webhook ingest from external tools; normalize raw events | No (writes to DB) | External APIs, Postgres, Redis | Internal job handlers |
| Normalization Pipeline (Workers) | Map raw events into canonical `trace_event` + `resource` + ACL deltas | No | Postgres, Redis | Internal job handlers |
| Entity Resolution (Workers) | Merge identities; infer KG entities/relationships | Yes (writes derived tables) | Postgres | Internal job handlers |
| Personal Graph Builder (Workers) | Build per-user timelines; cluster into tasks; enforce privacy boundaries | Yes (user-scoped) | Postgres, optional LLM plugin | Internal job handlers |
| Abstraction & Aggregation (Workers) | Create abstracted traces; enforce k-anonymity; compute patterns and variants | Yes | Postgres, optional vector | Internal job handlers |
| Context Graph Store (DB schema) | Persist probabilistic paths/variants/timing stats | Yes | Postgres | Queried via API |
| Observability (OTel + Prometheus) | Metrics, traces, logs correlation | N/A | OTel collector (optional), Prometheus | `/metrics`, trace export |
| CLI | Migrations, seed data, connector diagnostics | No | API/DB | `ocg` commands |

## Dependency direction rules (normative)
- UI MUST depend only on API contracts (OpenAPI) and MUST NOT access DB directly.
- API service MUST be the only public entrypoint; workers MUST NOT be publicly exposed.
- Workers MAY write to DB; workers MUST NOT call UI.
- Connectors MUST be read-only against external systems unless a future CHANGE_REQUEST explicitly enables writes.
- Derived-model writers (graph builders) MUST NOT modify raw ingestion tables except via documented pipelines.

### Forbidden coupling (normative)
- UI importing backend models directly (no shared ORM).
- Workers bypassing permission model by writing “public” derived outputs without k-anonymity checks.
- Any component reading connector secrets outside the connector subsystem.
- Any cross-user personal graph read path (except the user themselves) without explicit opt-in flag.

## Main flows (3–7), critical flows marked

### CF-1 (CRITICAL): Connector onboarding + permission sync
1. Admin configures connector credentials and enablement.
2. Connector runner performs scope validation (read-only), stores encrypted token, starts ingest.
3. Ingest creates `raw_event` and normalized `trace_event`, plus `resource` and `resource_acl` deltas.
4. Permission sync job refreshes group membership and ACLs on schedule.
5. Unknown ACL ⇒ mark `permission_state=UNKNOWN` ⇒ excluded from all user-visible outputs.

### CF-2 (CRITICAL): Permission-enforced dashboard query
1. User authenticates via OIDC; API maps user→principal IDs (user + groups).
2. API queries aggregated tables (`context_path_variant`, `context_edge`) joined with permission scope rules.
3. API returns abstracted, k-anonymous results; UI renders graphs/variants.

### CF-3 (CRITICAL): Personal timeline + task clustering (private)
1. Worker builds per-user ordered event stream from `trace_event`.
2. Worker clusters into `personal_task` with deterministic heuristics; optional LLM tagging if enabled.
3. UI queries personal endpoints scoped to authenticated user only.
4. User may opt-in to share abstracted traces; if not opted-in, user data MUST NOT enter aggregation.

### CF-4 (CRITICAL): K-anonymous aggregation → context graph update
1. Abstraction job converts eligible personal traces into `abstract_trace` (no identifiers).
2. Aggregator clusters abstract traces by similarity and process keys.
3. Publisher enforces k-anonymity thresholds and drops rare patterns.
4. Context graph tables updated via expand/contract-safe upserts.

### CF-5 (CRITICAL): Retention/deletion/export
1. Admin configures retention policy.
2. Scheduled purge deletes old raw/trace/personal/derived rows per rules.
3. Per-user export generates JSON/CSV bundle.
4. Per-user delete removes user-scoped data and triggers re-aggregation.

### CF-6 (CRITICAL): Suggestion API (“what happens next?”)
1. Caller provides process key + recent abstract step history.
2. API returns top next steps with probabilities and timing stats from `context_edge` and `context_path_variant`.
3. Response contains no raw text and no resource identifiers unless permission-allowed and configured.

## HOT_PATHS (HP) (normative)

### HP-0001: Analytics dashboard “process explorer” query
- Entrypoint: `GET /api/v1/analytics/processes/{process_key}/variants`
- Dependencies: Postgres (context tables), permission principal resolution
- Perf risks: heavy joins; large variant sets
- What is measured: p95/p99 endpoint latency, DB query time, rows scanned
- Required tracing spans:
  - `auth.resolve_principals`
  - `db.query.context_variants`
  - `perm.filter.aggregate`
- Gates: G-0003, G-0008

### HP-0002: Suggestion endpoint “next steps”
- Entrypoint: `POST /api/v1/suggest/next_steps`
- Dependencies: Postgres (edges), optional cache
- Perf risks: cold cache; poorly indexed edge lookups
- What is measured: p95/p99, cache hit rate, DB time
- Required tracing spans:
  - `auth.resolve_principals`
  - `db.query.context_edges`
- Gates: G-0003

### HP-0003: Ingestion normalize→trace write
- Entrypoint: connector job `ingest_batch(tool)`
- Dependencies: External API, Postgres, Redis
- Perf risks: rate limits; transaction bloat; duplicate events
- What is measured: events/sec, backlog depth, retry rate, API rate-limit errors
- Required tracing spans:
  - `connector.fetch`
  - `normalize.map_event`
  - `db.upsert.trace_event`
- Gates: G-0004, G-0008

### HP-0004: Permission sync refresh
- Entrypoint: scheduled job `sync_permissions(tool)`
- Dependencies: External API, Postgres
- Perf risks: slow directory APIs; inconsistent ACL formats
- What is measured: sync duration, stale ACL rate, unknown-permission count
- Required tracing spans:
  - `connector.fetch_acls`
  - `db.upsert.resource_acl`
- Gates: G-0001, G-0004

### HP-0005: Aggregation publish (abstract traces → context graph)
- Entrypoint: scheduled job `aggregate_context_graph()`
- Dependencies: Postgres, optional pgvector
- Perf risks: expensive clustering; long transactions; lock contention
- What is measured: job runtime, rows processed, k-anonymity drop rate, DB lock waits
- Required tracing spans:
  - `abstract.select_eligible`
  - `cluster.similarity`
  - `publish.upsert_context`
- Gates: G-0010, G-0004

## Diagram (normative)
```mermaid
flowchart TB
  U[User Browser] -->|OIDC Login| IDP[OIDC Provider]
  U -->|HTTPS| API[API Service (FastAPI)]
  API -->|SQL| PG[(PostgreSQL)]
  API -->|Jobs| RQ[(Redis Queue)]
  W1[Connector Workers] -->|Read APIs| EXT[External Tools]
  W1 -->|Jobs/SQL| RQ
  W1 -->|SQL| PG
  W2[Graph Workers] -->|SQL| PG
  W2 -->|Jobs| RQ
  API -->|metrics| PROM[/Prometheus/]
  W1 -->|metrics| PROM
  W2 -->|metrics| PROM
  API -->|traces| OTel[(OTel Collector optional)]
  W1 -->|traces| OTel
  W2 -->|traces| OTel
```

## Incident reading order (telemetry-first)
1. `dashboards/ingest`: backlog depth, connector error rate, rate-limit errors.
2. `dashboards/api`: p95 latency, 5xx rate, DB time, slow query logs.
3. `dashboards/db`: locks, bloat, top queries, index hit rate.
4. Traces: locate span with highest duration (`db.*`, `connector.fetch`).
5. Logs: correlated by `request_id` and `job_id` (no secrets).

## Change-safety notes
- Rollout/rollback hooks:
  - Feature flags for: raw content ingestion, LLM tagging, pgvector similarity, public bind.
  - Expand/contract migrations required.
    - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Expand/contract migrations (normative)

- Contract compatibility:
  - API is versioned under `/api/v1`; backwards compatible changes only without major version bump.
  - Derived tables are rebuildable; raw and normalized traces are the source of truth.
- Migration pointers:
  - Alembic migrations with reversible downgrade for schema-only changes.
  - For data backfills, use idempotent jobs with checkpointing.

## Implementation status snapshot (2026-02-08)
- API service implemented in `backend/ocg/main.py` with route modules in `backend/ocg/api`.
- Worker jobs implemented in `backend/ocg/workers/jobs.py` with queue names in `backend/ocg/workers/queues.py` and runtime orchestration in `backend/ocg/workers/runtime.py`.
- Docker Compose day-0 stack includes dedicated `workers` (RQ consumer) and `scheduler` (periodic enqueue) services in `docker-compose.yml`.
