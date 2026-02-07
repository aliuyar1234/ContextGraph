# Test Strategy — OCG (Open Context Graph)

## Determinism expectations (normative)
- Timeline ordering MUST be deterministic: sort by `(event_time, trace_event_id)`.
- Clustering MUST be deterministic by default:
  - deterministic heuristics first,
  - any probabilistic/LLM features MUST be feature-flagged and seeded/stabilized.

## What to test (normative)

### Unit tests
- Tool mapping: raw payload → normalized `trace_event` mapping.
- Permission logic: principal resolution, ACL evaluation, unknown-permission exclusion.
- Abstraction: `trace_event` → abstract steps without identifiers.
- K-anonymity enforcement logic.

### Integration tests (containerized)
- Postgres migrations (upgrade + downgrade for expand steps).
- Connector mock servers:
  - simulate rate limits, pagination, permission changes.
- API auth with test OIDC JWTs.
- End-to-end: ingest sample dataset → build graphs → query analytics.

### Security tests
- SAST/lint for injection risks.
- Log redaction scanner: ensure no tokens/emails (unless allowed).
- Negative permission tests:
  - user without ACL cannot see associated aggregates.

### Performance regression tests
- Perf smoke harness for HP-0001/HP-0002 endpoints.
- DB query plan checks for critical queries (explain analyze snapshots).

### Migration tests
- Expand/contract validation:
  - old API version still works after expand migration.
  - backfill job idempotency.

## What NOT to test
- Exact external tool behavior beyond connector contract (use mocks).
- UI pixel-perfect snapshot tests as PR blockers (allow evolution; focus on core flows).
- LLM output “semantic correctness” in CI (LLM is optional; keep offline eval separate).
