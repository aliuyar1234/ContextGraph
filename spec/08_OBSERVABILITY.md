# Observability — OCG (Open Context Graph)

## Correlation (normative)
- Every HTTP request MUST include `request_id`:
  - Accept inbound `X-Request-Id` or generate.
- Every job MUST include `job_id` and parent `request_id` when enqueued by API.
- Logs MUST be structured JSON and include:
  - `timestamp`, `level`, `service`, `request_id`, `job_id`, `user_id_hash` (if needed), `connector`, `event_type`.
- Redaction:
  - secrets and tokens MUST be removed.
  - emails SHOULD be hashed unless operator explicitly enables PII logs.

## Metrics (normative)
### API golden signals
- `http_requests_total{route,method,status}`
- `http_request_duration_seconds_bucket{route}`
- `http_5xx_rate`
- `db_query_duration_seconds_bucket{query_name}`
- `auth_failures_total`

### Ingestion golden signals
- `connector_fetch_duration_seconds{tool}`
- `connector_errors_total{tool,reason}`
- `ingest_events_total{tool}`
- `ingest_backlog_depth{queue}`
- `rate_limited_total{tool}`

### Aggregation/model signals
- `abstract_traces_created_total`
- `patterns_published_total`
- `patterns_dropped_k_anon_total`
- `aggregation_job_duration_seconds`
- `permission_unknown_records_total` (critical correctness signal)

## Traces (normative)
- OpenTelemetry tracing MUST be implemented for:
  - API endpoints in HP list.
    - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)

  - connector fetch and normalize spans.
  - aggregation pipeline stages.
- Required span attributes:
  - `tool`, `process_key` (when applicable), `db.statement_name`, `queue_name`.

## Dashboards (outline; normative)
- System health:
  - API latency/5xx, queue depth, worker saturation, DB locks.
- Connector health:
  - last successful sync, error rate, rate limits, backlog.
- Correctness proofs:
  - unknown permission count trend
  - k-anon drop rate
  - pattern publish counts
- Storage:
  - table sizes, growth/day, purge effectiveness.

## Alerts (normative baseline)
- High severity:
  - `permission_unknown_records_total` rising above operator threshold.
  - sustained 5xx rate for API.
  - queue depth continuously increasing.
  - connector auth failures (token invalid).
- Medium severity:
  - aggregation job duration regression
  - DB lock waits increase
  - purge job failures

## Signals that prove correctness (contracts C1–C5)
- C1 Correctness:
  - `permission_unknown_records_total` near-zero in steady state; spikes correlate to connector issues.
  - “permission test” synthetic checks succeed (see G-0001).
- C2 Security:
  - zero occurrences of redaction violations in log scan (G-0002).
  - zero public-bind-without-auth startups (config validation metric).
- C3 Performance:
  - perf harness trend stored as artifacts; regression gate enforced (G-0003).
- C4 Operability:
  - dashboards cover golden signals; runbook exists and referenced by alerts (G-0004, G-0011).
- C5 Change:
  - docs-as-code guard passes; migrations tested; dependency linter passes (G-0005, G-0007, G-0008).

## Implementation status snapshot (2026-02-07)
- Metrics instrumentation lives in `backend/ocg/core/observability.py`.
- Dashboards are defined in `ops/grafana/dashboards/system_health.json` and `ops/grafana/dashboards/connector_health.json`.
- Alert rules are defined in `ops/prometheus/alerts.yml`.
