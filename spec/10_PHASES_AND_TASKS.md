# Phases & Tasks — OCG (Open Context Graph)
Single ordered path: PHASE_0_BOOTSTRAP → DONE.

## PHASE_0_BOOTSTRAP (repo + CI + docs-as-code)
### T-0001 Initialize repository structure and licenses
- Purpose: Create the repo scaffold with SSOT docs and Apache-2.0 licensing.
- Acceptance criteria (binary):
  - `spec/` and Stage-1 docs are committed.
  - `LICENSE` present (Apache-2.0).
- Required evidence:
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: Fingerprint
- Implementation notes:
  - Create `backend/`, `frontend/`, `ops/`, `scripts/`, `spec/`, `docs/`, `migrations/`.

### T-0002 Define ONE repo-anchoring quality command
- Purpose: Establish a single local command that runs required checks.
- Acceptance criteria:
  - `make check` runs: format, lint, typecheck, unit tests, integration tests (optional profile), migration check, secret scan, redaction scan, perf-smoke (optional profile).
- Required evidence:
  - evidence: spec/11_QUALITY_GATES.md :: G-0006
- Implementation notes:
  - Implement `Makefile` targets calling `scripts/check.sh`.
  - Provide `CHECK_PROFILE=fast|ci|full`.

### T-0003 Wire CI (PR blocker) using the same command
- Purpose: Prevent drift by enforcing `make check` in CI.
- Acceptance criteria:
  - GitHub Actions workflow runs `make check CHECK_PROFILE=ci` on every PR and fails on violation.
- Required evidence:
  - evidence: spec/11_QUALITY_GATES.md :: G-0006
- Implementation notes:
  - Baseline CI provider GitHub Actions.
    - evidence: ASSUMPTIONS.md :: A-0003 CI provider baseline


### T-0004 Docs-as-code enforcement guard
- Purpose: Ensure changes to critical surfaces update SSOT docs and decisions.
- Acceptance criteria:
  - A guard script fails if:
    - API routes change without updating `spec/04_INTERFACES_AND_CONTRACTS.md`
    - DB schema changes without updating `spec/05_DATASTORE_AND_MIGRATIONS.md`
    - Security controls change without updating `spec/06_SECURITY_AND_THREAT_MODEL.md`
    - Hot paths change without updating `spec/02_ARCHITECTURE.md`
    - Any of the above changes without a new entry in `DECISIONS.md` or `ASSUMPTIONS.md` when applicable
- Required evidence:
  - evidence: spec/11_QUALITY_GATES.md :: G-0007
- Implementation notes:
  - Implement `scripts/docs_guard.sh` comparing OpenAPI + Alembic heads + key files.

## PHASE_1_CORE_PLATFORM (API, DB, auth)
### T-0005 Implement Postgres schema + migrations (Alembic)
- Purpose: Create the core tables and indexes.
- Acceptance criteria:
  - `ocg migrate up` creates all tables listed in spec/05.
  - Fresh install passes integration tests.
- Required evidence:
  - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Schema overview
  - evidence: spec/11_QUALITY_GATES.md :: G-0005
- Implementation notes:
  - Use SQLAlchemy models or explicit SQL; ensure indexes exist.

### T-0006 Implement API service skeleton with health/metrics
- Purpose: Run a minimal API with OTel/Prometheus endpoints.
- Acceptance criteria:
  - `/healthz`, `/readyz`, `/metrics` work in dev compose.
- Required evidence:
  - evidence: spec/08_OBSERVABILITY.md :: Metrics
- Implementation notes:
  - FastAPI + dependency-injected DB session.

### T-0007 Implement OIDC auth + RBAC
- Purpose: Secure the API/UI.
- Acceptance criteria:
  - Valid JWT required for non-health endpoints.
  - RBAC enforced for admin endpoints.
- Required evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AuthN/AuthZ
  - evidence: spec/11_QUALITY_GATES.md :: G-0002
- Implementation notes:
  - Provide dev-only auth flag; production fails if misconfigured.

## PHASE_2_CONNECTORS_AND_NORMALIZATION
### T-0008 Implement connector framework + secret refs
- Purpose: Standardize connectors with fail-closed behavior.
- Acceptance criteria:
  - Connector configs store only secret refs (no plaintext tokens).
  - Read-only scopes validation implemented.
- Required evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Secrets handling
- Implementation notes:
  - Connector interface: `validate()`, `fetch_events()`, `fetch_acls()`, `normalize()`.

### T-0009 Implement Slack connector (metadata-only)
- Purpose: Ingest chat/channel events and ACLs.
- Acceptance criteria:
  - Ingests events into `raw_event` and `trace_event`.
  - Produces `resource` + `resource_acl`.
  - Unknown ACL ⇒ excluded from user-facing queries.
- Required evidence:
  - evidence: spec/02_ARCHITECTURE.md :: CF-1
- Implementation notes:
  - Message bodies OFF by default; store only event metadata.

### T-0010 Implement Jira connector
- Purpose: Ingest ticket transitions and comment metadata.
- Acceptance criteria: same as T-0009.
- Required evidence:
  - evidence: spec/02_ARCHITECTURE.md :: HP-0003
- Implementation notes:
  - Comment bodies OFF by default.

### T-0011 Implement GitHub connector
- Purpose: Ingest PR events and repo metadata.
- Acceptance criteria: same as T-0009.
- Required evidence:
  - evidence: spec/02_ARCHITECTURE.md :: CF-1

## PHASE_3_KG_AND_IDENTITY
### T-0012 Implement identity resolution (baseline rules)
- Purpose: Merge users across tools.
- Acceptance criteria:
  - `identity` records map to `person`.
  - Principal membership computed for groups.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: ### Identity
  - evidence: spec/03_DOMAIN_MODEL.md :: ### Principal
  - evidence: spec/11_QUALITY_GATES.md :: G-0001
- Implementation notes:
  - Baseline: email matching + tool directory mapping; log confidence.

### T-0013 Implement KG entity inference (baseline)
- Purpose: Create canonical entities and relationships.
- Acceptance criteria:
  - Entities and edges present for at least `Person`, `Project`, `Product`, `Service` when inferable.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: KnowledgeEntity / KnowledgeEdge

## PHASE_4_PERSONAL_GRAPH (private) + OPT-IN
### T-0014 Implement personal timeline builder
- Purpose: Build deterministic per-user timelines.
- Acceptance criteria:
  - Timeline endpoints return only caller’s data.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: PersonalTimelineItem
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0002

### T-0015 Implement task clustering (heuristics-first)
- Purpose: Cluster timeline into tasks.
- Acceptance criteria:
  - Task list stable across repeated runs on same dataset.
- Required evidence:
  - evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations
- Implementation notes:
  - Optional LLM tagging behind feature flag.
    - evidence: DECISIONS.md :: D-0010 LLM tagging is optional and OFF by default


### T-0016 Implement explicit opt-in toggle
- Purpose: Control aggregation eligibility.
- Acceptance criteria:
  - Default opt-in = false; user can enable and revoke.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules

## PHASE_5_CONTEXT_GRAPH (aggregation + suggestions)
### T-0017 Implement abstraction pipeline (no identifiers)
- Purpose: Convert personal tasks/traces into abstract traces.
- Acceptance criteria:
  - Abstract traces contain no raw text, no user IDs, no resource IDs/URLs.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: AbstractTrace
  - evidence: spec/11_QUALITY_GATES.md :: G-0009

### T-0018 Implement clustering + k-anonymity publish gate
- Purpose: Produce published patterns only when safe.
- Acceptance criteria:
  - Patterns not meeting thresholds are not published and not queryable.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules
  - evidence: spec/11_QUALITY_GATES.md :: G-0010

### T-0019 Build context edges + path variants + timing stats
- Purpose: Build probabilistic path model and top variants.
- Acceptance criteria:
  - `context_edge` probabilities normalized; `context_path_variant` top-K present.
- Required evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: ### ContextEdge (probabilistic next-step model)
  - evidence: spec/03_DOMAIN_MODEL.md :: ### ContextPathVariant

### T-0020 Implement suggestion API
- Purpose: Provide “next steps” endpoint.
- Acceptance criteria:
  - Endpoint returns top-N next steps for a given process key without leaks.
- Required evidence:
  - evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: Suggestions

## PHASE_6_UI_DASHBOARDS + OPS
### T-0021 Implement Admin UI: connectors + health + retention
- Purpose: Make system operable.
- Acceptance criteria:
  - Admin can enable/disable connectors; view health; configure retention.
- Required evidence:
  - evidence: spec/12_RUNBOOK.md :: Day-0: minimal dev run (Docker Compose)

### T-0022 Implement Analytics UI: process explorer + variants + bottlenecks
- Purpose: Impressive dashboards for mid-market value.
- Acceptance criteria:
  - UI renders variants and bottlenecks for a process key.
- Required evidence:
  - evidence: spec/02_ARCHITECTURE.md :: HP-0001

### T-0023 Implement Personal UI: timeline + tasks + opt-in
- Purpose: Personal value and privacy.
- Acceptance criteria:
  - User sees own timeline/tasks; can opt-in/out.
- Required evidence:
  - evidence: spec/02_ARCHITECTURE.md :: CF-3

### T-0024 Observability dashboards + alerts + runbook completion
- Purpose: Operator-ready.
- Acceptance criteria:
  - Grafana dashboards present; top alerts configured; runbook has top 5 incidents.
- Required evidence:
  - evidence: spec/08_OBSERVABILITY.md :: Dashboards
  - evidence: spec/12_RUNBOOK.md :: Top 5 incident playbooks

## DONE (phase exit criteria)
All gates MUST pass in CI:
- G-0001..G-0012.
  - evidence: spec/11_QUALITY_GATES.md :: Gate format

