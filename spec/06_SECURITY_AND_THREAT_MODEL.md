# Security & Threat Model — OCG (Open Context Graph)

## Security posture (normative)
- Deny-by-default everywhere.
- Least privilege:
  - Separate DB roles for API, workers, and migrations.
  - Connectors are read-only at external tools.
- Secrets never in repo; stored encrypted at rest; redacted from logs.
- Unknown permissions ⇒ exclude from user-visible views.
- Aggregation enforces k-anonymity and removes identifiers and raw text.

## AuthN/AuthZ (normative)
### AuthN
- Production mode MUST use OIDC JWT validation.
- Dev-only auth MAY exist but MUST be disabled by default and MUST warn prominently when enabled.
- Public bind without OIDC configured MUST FAIL TO START.
  - evidence: spec/02_ARCHITECTURE.md :: Dependency direction rules (normative)


### AuthZ
Authorization is layered:
1. RBAC (admin/analyst/user) gates endpoints and UI areas.
2. Permission filtering gates data access:
   - Resource-level ACLs evaluated via principal membership.
   - If resource/trace permission_state != KNOWN ⇒ excluded from all user-visible queries.

## Trust boundaries (normative)
```mermaid
flowchart LR
  subgraph Z1[Trust Zone: User Device]
    B[Browser]
  end

  subgraph Z2[Trust Zone: OCG App Network]
    API[API Service]
    W[Workers]
    RQ[Redis Queue]
  end

  subgraph Z3[Trust Zone: Data Store]
    PG[(PostgreSQL)]
  end

  subgraph Z4[Trust Zone: External Systems]
    IDP[OIDC Provider]
    EXT[Slack/Jira/GitHub/...]
  end

  B -->|HTTPS| API
  API -->|JWT verify| IDP
  API -->|SQL| PG
  API -->|enqueue| RQ
  W -->|dequeue| RQ
  W -->|SQL| PG
  W -->|HTTPS (read-only)| EXT
```

Trust crossings:
- Browser→API (internet/internal): MUST use TLS; MUST require auth.
- API/Workers→DB: MUST use credentials with least privilege; MUST use TLS where supported.
- Workers→External tools: MUST use read-only scopes; MUST handle rate limiting.

## Secrets handling (normative)
- Secrets MUST be provided via:
  - environment variables,
  - mounted secret files,
  - or Kubernetes secrets.
- `connector_config.config_json` MUST store only secret references (e.g., `env:JIRA_TOKEN`), never plaintext.
- Logs MUST redact:
  - Authorization headers
  - tokens/keys
  - emails (unless operator enables PII logging explicitly; default OFF)

## TOP_ABUSE_CASES (AC) (>=10; normative)

### AC-0001: Unauthorized user reads restricted resources via analytics
- Goal: see traces/patterns derived from resources not permitted.
- Entrypoint: `/api/v1/analytics/*`
- Impact: data leakage.
- Controls: permission_state gating; ACL join; k-anonymity for aggregates.
- Verification: G-0001, G-0010.

### AC-0002: Admin views personal timelines of employees (surveillance)
- Goal: inspect private work details.
- Entrypoint: personal endpoints.
- Impact: privacy violation, trust loss.
- Controls: personal endpoints strictly `person_id == caller`; no admin override by default.
- Verification: G-0001, G-0002.

### AC-0003: Connector token exfiltration via logs
- Goal: obtain external API tokens.
- Entrypoint: worker logs, crash dumps.
- Impact: full tool compromise.
- Controls: secret refs only; redaction; structured logging; no debug dumps with env.
- Verification: G-0002.

### AC-0004: Pattern re-identification via rare traces
- Goal: infer a specific person’s workflow.
- Entrypoint: aggregated dashboards.
- Impact: privacy breach.
- Controls: k-anonymity thresholds; drop rare patterns; bucket timing/outcomes; no identities.
- Verification: G-0010.

### AC-0005: Public exposure without auth
- Goal: access UI/API over public network unauthenticated.
- Entrypoint: misconfigured bind.
- Impact: data breach.
- Controls: fail-to-start if bind non-local and OIDC missing; secure defaults.
- Verification: G-0002, G-0011.

### AC-0006: SQL injection / query manipulation
- Goal: execute arbitrary SQL.
- Entrypoint: API query params.
- Impact: data exfiltration/alteration.
- Controls: parameterized queries/ORM; input validation; least-priv DB roles.
- Verification: G-0002.

### AC-0007: Permission sync staleness exploited
- Goal: user keeps access after losing tool permission.
- Entrypoint: stale ACL cache.
- Impact: unauthorized access.
- Controls: periodic ACL sync; “stale ACL” TTL; fail closed on ACL uncertainty.
- Verification: G-0001, G-0004.

### AC-0008: Worker retry storm causes DoS
- Goal: degrade availability and increase cost.
- Entrypoint: external rate limits or bad payloads.
- Impact: outage.
- Controls: bounded retries with backoff; dead-letter queue; circuit breaker per connector.
- Verification: G-0004, G-0008.

### AC-0009: Malicious connector config injects exfil endpoints
- Goal: send data to attacker.
- Entrypoint: connector config.
- Impact: data exfiltration.
- Controls: no outbound webhooks by default; allowlist external tool domains; config validation.
- Verification: G-0002.

### AC-0010: LLM plugin leaks data externally
- Goal: send sensitive metadata to remote LLM.
- Entrypoint: task labeling/summarization.
- Impact: data leakage.
- Controls: LLM feature OFF by default; explicit enable; “local-only” mode; payload minimization; audit log.
- Verification: G-0002, G-0009.

## Least privilege plan (normative)
- Postgres roles:
  - `ocg_api`: SELECT on most tables, INSERT on audit, no DDL.
  - `ocg_worker`: INSERT/UPDATE on ingestion + derived tables, no DDL.
  - `ocg_migrate`: DDL for migrations only.
- External tool scopes MUST be read-only; write scopes MUST be rejected at validation time.

## Audit logging (normative)
- Record admin actions:
  - connector enable/disable, retention changes, auth config changes.
- Audit log MUST NOT include secrets or raw content.

## Implementation status snapshot (2026-02-07)
- OIDC JWT validation + RBAC implemented in `backend/ocg/core/security.py` and `backend/ocg/api/deps.py`.
- Non-local bind fail-closed startup validation implemented in `validate_startup_security`.
- Dev-header auth mode requires explicit `OCG_DEV_AUTH_ENABLED=true` and is intended for local/demo workflows.
