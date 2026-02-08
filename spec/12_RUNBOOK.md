# Runbook — OCG (Open Context Graph)

## Day-0: minimal dev run (Docker Compose)
### Prereqs
- Docker + Docker Compose
- Make
- Python 3.11+ and Node 20+ (if running outside containers)

### Steps
1. Start stack:
   - `docker compose up -d postgres redis`
   - `docker compose up -d api workers scheduler ui`
2. Run migrations:
   - `ocg migrate up`
3. Seed sample data (dev only):
   - `ocg seed demo`
4. Verify health:
   - `curl -f http://127.0.0.1:8080/healthz`
   - `curl -f http://127.0.0.1:8080/readyz`
   - `curl -f http://127.0.0.1:8080/metrics | head`
5. Open UI:
   - `http://127.0.0.1:3000`
6. Verify “happy path”:
   - Analytics page shows at least one published pattern (from demo seed).
   - Personal page shows timeline/tasks for demo user.

## How to run quality gates locally
- Primary command:
  - `make check CHECK_PROFILE=fast`
- CI-equivalent:
  - `make check CHECK_PROFILE=ci`
- Full suite:
  - `make check CHECK_PROFILE=full`

Interpreting failures:
- `docs_guard` failure: update SSOT docs + DECISIONS/ASSUMPTIONS.
- migration failure: fix Alembic scripts and expand/contract ordering.
- permission tests: fix ACL joins or unknown-permission exclusion.
- frontend build failure (ci/full): run `npm --prefix frontend ci && npm --prefix frontend run build` locally and fix TS/Next build issues.

## Operational toggles (feature flags) with safe defaults
- `FEATURE_RAW_CONTENT=false` (safe default)
- `FEATURE_LLM_TAGGING=false` (safe default)
- `FEATURE_PGVECTOR=false` (safe default)
- `SERVER_BIND=127.0.0.1` (safe default)
- `AUTH_MODE=oidc` required for non-local bind
- `RETENTION_ENABLED=true` (baseline); if disabled, system MUST stop publishing aggregates and warn

## Top 5 incident playbooks

### Incident 1: Connector ingestion backlog growing
- Signals:
  - `ingest_backlog_depth{queue}` increasing
  - `connector_errors_total` rising
- Triage:
  1) Check rate limit errors.
  2) Check queue worker saturation.
  3) Check DB locks and slow upserts.
- Mitigations:
  - Reduce poll frequency; open circuit breaker cooldown.
  - Scale connector workers.
  - Temporarily pause aggregation jobs.
- Rollback:
  - Disable connector via admin UI (no data loss; ingestion stops).

### Incident 2: Spike in unknown permissions (risk of data exclusion)
- Signals:
  - `permission_unknown_records_total` rising
- Triage:
  1) Identify tool/connector causing unknown ACLs.
  2) Check permission sync job failures.
- Mitigations:
  - Force permission sync now.
  - Fix connector scope/config.
- Rollback:
  - Disable affected connector; keep system safe (data excluded).

### Incident 3: Analytics endpoints slow / timeouts
- Signals:
  - API p95 latency spike; DB time high; lock waits
- Triage:
  1) Check top queries and missing indexes.
  2) Check variant set size; apply pagination.
- Mitigations:
  - Add/adjust indexes; enable cached aggregates; increase statement timeout cautiously.
- Rollback:
  - Roll back recent release; keep migrations expand-only to allow rollback.

### Incident 4: Failed purge / storage growth
- Signals:
  - table size growth; purge job failures
- Triage:
  1) Check retention config validity.
  2) Check DB permissions for purge job.
- Mitigations:
  - Run purge manually; vacuum/analyze.
- Rollback:
  - Temporarily increase storage; disable non-critical connectors to slow growth.

### Incident 5: Auth misconfiguration after deploy
- Signals:
  - sudden `401/403` across UI/API; startup failures if public bind
- Triage:
  1) Validate OIDC issuer/audience keys.
  2) Check clock skew.
- Mitigations:
  - Reapply correct config; restart.
- Rollback:
  - Revert config to last known good; keep bind local until fixed.

## Implementation status snapshot (2026-02-08)
- Compose file: `docker-compose.yml`
- Backend CLI: `python -m ocg.cli migrate up`, `python -m ocg.cli seed demo`, `python -m ocg.cli diagnostics connectors`
- Worker runtime CLI: `python -m ocg.cli worker run`, `python -m ocg.cli worker scheduler`, `python -m ocg.cli worker tick`
- Frontend build command: `npm --prefix frontend run build`
