# Reliability & Operations — OCG (Open Context Graph)

## Reliability principles (normative)
- Timeouts everywhere.
- Retries only when idempotent; bounded with exponential backoff and jitter.
- Bulkheads per connector/tool to avoid cascading failure.
- Backpressure: ingestion must slow down when DB/queue pressure rises.
- Degradation: analytics can be stale; system must not crash.

## Timeouts (normative)
- External API calls:
  - connect timeout MUST be set.
  - read timeout MUST be set.
  - total request budget SHOULD be <= 15s per call.
- DB queries:
  - API queries SHOULD have statement timeout (e.g., 5–10s) configurable.
  - Worker batch queries MAY be longer but MUST be bounded and chunked.
- Job execution:
  - Each job type MUST have a max runtime; on exceed, job MUST be canceled and moved to dead-letter with reason.

## Retry rules (normative)
- Ingestion fetch:
  - Retryable: 429/5xx/timeouts
  - Non-retryable: 4xx (except 429)
  - Max attempts: configurable; default small (assumption-driven).
- Normalize/write:
  - Upserts MUST be idempotent; safe to retry.
- Permission sync:
  - Retry with backoff; if repeated failure, mark connector degraded and alert.

## Backpressure & circuit breakers (normative)
- Queue depth thresholds MUST trigger:
  - reduced polling frequency,
  - pausing non-critical jobs (e.g., full re-aggregation),
  - and emitting alerts.
- Circuit breaker per connector:
  - On sustained failures, open circuit and stop calling external API for cooldown period.

## Bulkheads (normative)
- Separate worker pools/queues:
  - `connector_ingest`
  - `normalize`
  - `permissions_sync`
  - `personal_graph`
  - `aggregate_context`
- A failure in one queue MUST NOT prevent API availability.

## Degradation modes (normative)
- If aggregation is behind:
  - UI MUST show “data freshness” and allow users to continue with stale aggregates.
- If permissions are unknown/stale:
  - system MUST exclude affected data rather than risk leakage.
- If Postgres is read-only / under pressure:
  - API may return 503 with `retryable=true` for analytics endpoints; personal endpoints should also degrade safely.

## Rollout/rollback assumptions
- Deployments are immutable containers.
- Schema migrations are run as a separate step with `ocg migrate up`.
- Rollback plan:
  - rollback app first if migration is backward compatible,
  - if migration is not backward compatible, MUST use expand/contract to avoid needing DB rollback.
- Feature flags MUST be used for riskier features:
  - raw content ingestion
  - LLM tagging
  - pgvector similarity
  - public bind
