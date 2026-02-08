# Interfaces & Contracts — OCG (Open Context Graph)

## Public surfaces
- Web UI (HTTP)
- REST API `/api/v1/*` (HTTP/JSON)
- CLI `ocg` (local)
- Operational endpoints:
  - `/healthz` (liveness)
  - `/readyz` (readiness: DB + Redis reachable)
  - `/metrics` (Prometheus)

## REST API (normative)

### Auth
- API MUST validate OIDC JWTs (aud/iss/exp) and map to internal `person_id`.
- Dev-only mode MAY exist but MUST be disabled by default in production builds.
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AuthN/AuthZ (normative)


### Core endpoints (v1)
#### Connectors (admin only)
- `GET /api/v1/admin/connectors`
- `POST /api/v1/admin/connectors/{tool}/enable`
- `POST /api/v1/admin/connectors/{tool}/disable`
- `POST /api/v1/admin/connectors/{tool}/sync_now`
- `GET /api/v1/admin/connectors/{tool}/health`

Example: enable Jira
```json
POST /api/v1/admin/connectors/jira/enable
{
  "base_url": "https://jira.example.com",
  "auth": { "type": "api_token", "token_ref": "env:JIRA_TOKEN" },
  "projects": ["ENG", "SRE"],
  "poll_interval_seconds": 120
}
```

#### Personal (user-scoped)
- `GET /api/v1/personal/timeline?from=...&to=...`
- `GET /api/v1/personal/tasks?from=...&to=...`
- `POST /api/v1/personal/opt_in_aggregation` (explicit opt-in toggle)

Example response: tasks
```json
{
  "tasks": [
    {
      "personal_task_id": "pt_01H...",
      "label": "investigate_alert",
      "start_time": "2026-02-07T09:01:00Z",
      "end_time": "2026-02-07T10:12:00Z",
      "confidence": 0.72
    }
  ]
}
```

#### Analytics (k-anonymous, abstracted)
- `GET /api/v1/analytics/processes` (list process keys)
- `GET /api/v1/analytics/processes/{process_key}/patterns`
- `GET /api/v1/analytics/patterns/{pattern_id}/variants`
- `GET /api/v1/analytics/patterns/{pattern_id}/edges`
- `GET /api/v1/analytics/patterns/{pattern_id}/bottlenecks`

Example: variants
```json
{
  "pattern_id": "cp_01H...",
  "k_anonymous": true,
  "variants": [
    {
      "rank": 1,
      "frequency": 0.31,
      "steps": [
        { "action_type": "escalate", "tool_family": "chat", "process_tags": ["war_room"] },
        { "action_type": "comment", "tool_family": "tickets", "process_tags": ["triage"] },
        { "action_type": "resolve", "tool_family": "tickets", "process_tags": ["close_out"] }
      ],
      "timing": { "p50_seconds": 1800, "p95_seconds": 14400 },
      "outcomes": { "resolved_fast": 0.62, "resolved_slow": 0.38 }
    }
  ]
}
```

#### Suggestions (read-only)
- `POST /api/v1/suggest/next_steps`

Request:
```json
{
  "process_key": "incident:service=payments:severity=P1",
  "recent_steps": [
    { "action_type": "escalate", "tool_family": "chat" },
    { "action_type": "comment", "tool_family": "tickets" }
  ],
  "limit": 5
}
```

Response:
```json
{
  "next_steps": [
    {
      "step": { "action_type": "deploy", "tool_family": "code", "process_tags": ["mitigation"] },
      "probability": 0.27,
      "expected_time_to_next_seconds": 900
    }
  ]
}
```

## Error model (normative)
### Standard error envelope
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Not authorized.",
    "retryable": false,
    "request_id": "req_01H...",
    "trace_id": "0123456789abcdef0123456789abcdef"
  }
}
```

### Retryable vs non-retryable
- Retryable:
  - `429 RATE_LIMITED` (with `retry_after_ms`)
  - `503 DEPENDENCY_UNAVAILABLE`
  - `504 TIMEOUT`
- Non-retryable:
  - `400 INVALID_ARGUMENT`
  - `401 UNAUTHENTICATED`
  - `403 PERMISSION_DENIED`
  - `404 NOT_FOUND`
  - `409 CONFLICT` (unless documented idempotency key applies)

### Idempotency and dedup (normative)
- Ingestion writes MUST be idempotent:
  - `raw_event` uniqueness: `(tool, external_event_id)` unique.
  - `trace_event` uniqueness: `(tool, external_event_id)` unique.
- Background jobs MUST use deterministic job keys to prevent duplication.
- API endpoints are read-only (v1) and thus safe to retry.

### Ordering semantics
- Trace events MUST preserve tool event timestamps, but ingestion MAY arrive out of order.
- Timeline builder MUST sort by `(event_time, trace_event_id)` for determinism.

## Versioning + backwards compatibility (normative)
- REST API version in path: `/api/v1`.
- Backwards compatible changes MAY include:
  - additive fields
  - new endpoints
  - new enum values with safe fallbacks
- Breaking changes MUST bump major version (`/api/v2`) and provide migration notes.
- Deprecation:
  - MUST be announced in release notes.
  - MUST remain for at least 2 minor releases unless security requires faster removal.

## Implementation status snapshot (2026-02-08)
- API implementation baseline exists in `backend/ocg/main.py` and routers under `backend/ocg/api/*`.
- OpenAPI baseline artifact is tracked at `docs/openapi/openapi.v1.json` and checked by `scripts/openapi_check.sh`.
- CI compatibility guard uses the same command path via `make check CHECK_PROFILE=ci`.
- Error envelopes include both `request_id` and `trace_id` for cross-system correlation.
