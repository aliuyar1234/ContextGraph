# OCG SSOT Pack (for Codex / AI coding agents)

This ZIP is a **Single Source of Truth (SSOT)** for implementing **OCG (Open Context Graph)** end-to-end with deterministic decisions, fail-closed defaults, and drift resistance. It contains **specifications only** (no implementation code).

## How to start (operator / implementer)
1) Read the precedence rules (below) and obey them.
2) Execute tasks in:
   - evidence: spec/10_PHASES_AND_TASKS.md :: PHASE_0_BOOTSTRAP
3) Use gates as “definition of done”:
   - evidence: spec/11_QUALITY_GATES.md :: Gate format
4) Use the runbook to validate the minimal happy path:
   - evidence: spec/12_RUNBOOK.md :: Day-0: minimal dev run (Docker Compose)

## Precedence order (MUST be applied verbatim)
1) AGENTS.md
2) CONSTITUTION.md
3) spec/* (numeric order; existing files only)
4) DECISIONS.md
5) ASSUMPTIONS.md
6) README.md
7) templates/*, checks/*, runbook content

## Where to find X (index)
- Goals / constraints / must-not-happen: evidence: spec/00_PROJECT_FINGERPRINT.md :: Canonical summary (1 screen)
- Scope boundaries and MVP: evidence: spec/01_SCOPE.md :: MVP definition (ship threshold)
- Architecture components + hot paths: evidence: spec/02_ARCHITECTURE.md :: Component boundary table (normative)
- Domain objects (traces, patterns, graphs): evidence: spec/03_DOMAIN_MODEL.md :: Key domain objects (fields are conceptual; storage in spec/05)
- Public API contracts + examples: evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: REST API (normative)
- DB schema + migrations + retention: evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Schema overview (normative)
- Security posture + trust boundaries + abuse cases: evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: TOP_ABUSE_CASES (AC) (>=10; normative)
- Reliability semantics (timeouts/retries/bulkheads): evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Reliability principles (normative)
- Observability signals and dashboards: evidence: spec/08_OBSERVABILITY.md :: Dashboards (outline; normative)
- Test expectations and determinism rules: evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations (normative)
- Implementation plan (single path): evidence: spec/10_PHASES_AND_TASKS.md :: Single ordered path: PHASE_0_BOOTSTRAP → DONE.
- Quality gates (binary): evidence: spec/11_QUALITY_GATES.md :: Gate format
- Day-0 run + incident playbooks: evidence: spec/12_RUNBOOK.md :: Top 5 incident playbooks
- Decision log: evidence: DECISIONS.md :: Decisions (append-only)
- Assumptions log: evidence: ASSUMPTIONS.md :: Assumptions (append-only)
- Open questions: evidence: QUESTIONS_FOR_USER.md :: Questions for user (non-blocking unless explicitly marked)
- Drift / manifest rules: evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## System tour (15 minutes)
- Product surfaces:
  - Web UI dashboards and admin: evidence: spec/00_PROJECT_FINGERPRINT.md :: Product shape
  - REST API (`/api/v1/*`): evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: Public surfaces
  - CLI `ocg` (migrations/seed/diagnostics): evidence: spec/02_ARCHITECTURE.md :: Component boundary table (normative)
- Critical flows (risk-bearing):
  - CF-1 connector onboarding + permission sync: evidence: spec/02_ARCHITECTURE.md :: CF-1 (CRITICAL)
  - CF-2 permission-enforced dashboards: evidence: spec/02_ARCHITECTURE.md :: CF-2 (CRITICAL)
  - CF-3 personal timeline privacy boundary: evidence: spec/02_ARCHITECTURE.md :: CF-3 (CRITICAL)
  - CF-4 k-anonymous aggregation publish: evidence: spec/02_ARCHITECTURE.md :: CF-4 (CRITICAL)
  - CF-5 retention/deletion/export: evidence: spec/02_ARCHITECTURE.md :: CF-5 (CRITICAL)
  - CF-6 next-step suggestions: evidence: spec/02_ARCHITECTURE.md :: CF-6 (CRITICAL)
- Where performance matters:
  - Analytics query: evidence: spec/02_ARCHITECTURE.md :: HP-0001: Analytics dashboard “process explorer” query
  - Suggestions endpoint: evidence: spec/02_ARCHITECTURE.md :: HP-0002: Suggestion endpoint “next steps”
- How to validate the minimal path:
  - Run stack + seed demo + verify UI endpoints: evidence: spec/12_RUNBOOK.md :: Day-0: minimal dev run (Docker Compose)
- How to validate quality:
  - Gates define pass/fail: evidence: spec/11_QUALITY_GATES.md :: Gate format
  - Checks index defines how to run and interpret: evidence: checks/CHECKS_INDEX.md :: Checks overview

## Change map (top 10): If you change X, update Y (and re-run checks)
1) API routes / request/response shapes → update: evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: REST API (normative)
2) AuthN/AuthZ model → update: evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AuthN/AuthZ (normative)
3) Permission filtering logic → update: evidence: spec/03_DOMAIN_MODEL.md :: Permission and privacy invariants (normative)
4) DB schema / indexes → update: evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Schema overview (normative)
5) Migrations discipline → update: evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Expand/contract migrations (normative)
6) Retry/timeout behavior → update: evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Retry rules (normative)
7) Aggregation/k-anonymity rules → update: evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules (normative)
8) Hot paths or perf budgets → update: evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)
9) Logs/metrics/traces schema → update: evidence: spec/08_OBSERVABILITY.md :: Correlation (normative)
10) Any critical flow semantics → update: evidence: spec/02_ARCHITECTURE.md :: Main flows (3–7), critical flows marked

## Drift detection and MANIFEST
- MANIFEST.sha256 is the integrity root for this pack.
- Any change to any file requires:
  1) updating CHANGELOG.md and AUDIT_REPORT.md,
  2) regenerating MANIFEST.sha256,
  3) and re-running reference integrity checks.
- Verification check:
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## Implementation snapshot (2026-02-07)
- Backend/API + workers + CLI implemented under `backend/`.
- Frontend dashboards implemented under `frontend/`.
- Ops assets (compose/prometheus/grafana) implemented under `docker-compose.yml` and `ops/`.
- Quality anchor command: `make check CHECK_PROFILE=fast|ci|full`.
