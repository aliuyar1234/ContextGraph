# CHANGELOG.md — SSOT Pack Changes

This changelog tracks changes to the SSOT pack itself (docs, structure, gates, checks), not product implementation code.

## v1 (initial pack)
- Introduced canonical SSOT structure, precedence rules, and drift detection via MANIFEST.
  - Related decisions: evidence: DECISIONS.md :: D-0001 Primary datastore is PostgreSQL + Alembic
- Added project-tailored CONSTITUTION.md and slop blacklist enforcement mapping.
  - Related assumptions: evidence: ASSUMPTIONS.md :: A-0007 No prior engineering constitution existed in chat

## v1.1 (audit patch)
- Fixed evidence pointer strictness issues:
  - removed non-resolving evidence-format examples from checks
  - rewrote spec/11 QAC + SB enforcement maps to avoid table-inline evidence pointers
  - normalized inline evidence pointers to standalone lines with resolvable phrases
  - evidence: checks/CHECKS_INDEX.md :: CHK-REF-INTEGRITY
- Regenerated MANIFEST.sha256 after patch (integrity root updated).
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## v1.2 (phase-0 bootstrap start)
- Started implementation for PHASE_0 by completing T-0001:
  - added repository scaffold directories: `backend/`, `frontend/`, `ops/`, `scripts/`, `docs/`, `migrations/`
  - added `LICENSE` with Apache License 2.0 text
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0001 Initialize repository structure and licenses
- Updated progress tracking and regenerated MANIFEST after structural additions.
  - evidence: PROGRESS.md :: Task status table
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## v1.3 (phase-0 quality anchoring)
- Completed T-0002 by introducing one repository-level quality command path:
  - added `Makefile` with `make check CHECK_PROFILE=<fast|ci|full>`
  - added `scripts/check.sh` with staged checks (format, lint, typecheck, unit, integration profile-gated, migration, secret scan, redaction scan, perf-smoke profile-gated)
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0002 Define ONE repo-anchoring quality command
- Completed T-0003 by wiring CI to the same quality anchor command.
  - added `.github/workflows/ci.yml` and PR trigger running `make check CHECK_PROFILE=ci`
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0003 Wire CI (PR blocker) using the same command
- Completed T-0004 by adding docs-as-code guard enforcement.
  - added `scripts/docs_guard.sh` and `scripts/lint.sh`
  - guard enforces required spec updates for API/schema/security/hot-path changes and decision/assumption updates on critical-surface edits
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0004 Docs-as-code enforcement guard

## v2.0 (full implementation against PHASE_1..PHASE_6)
- Implemented T-0005..T-0024 end-to-end with a runnable MVP stack.
  - Backend: FastAPI API, OIDC/RBAC, SQLAlchemy models, Alembic migrations, CLI (`ocg`), connectors (Slack/Jira/GitHub), workers, personal graph, abstraction/aggregation, suggestion API.
  - Frontend: Next.js admin/analytics/personal dashboards.
  - Ops: Docker Compose stack, Prometheus config + alerts, Grafana dashboard JSONs.
  - evidence: PROGRESS.md :: Task status table
- Added tests and verification harnesses:
  - unit/integration suites under `backend/tests/*`
  - migration safety test and end-to-end pipeline test
  - OpenAPI baseline export and compatibility check script
  - dependency boundary linter and perf-smoke harness
  - evidence: backend/tests/integration/test_end_to_end_pipeline.py :: test_ingest_to_analytics_pipeline
- Updated SSOT governance and implementation snapshots:
  - decision log and assumptions updated for implementation-specific choices
  - relevant spec snapshots updated (architecture/interfaces/datastore/security/observability/runbook)
  - manifest regenerated after all changes
  - evidence: DECISIONS.md :: D-0013 Dev-header auth override exists only behind explicit flag
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## v2.1 (documentation professionalism refresh)
- Replaced root `README.md` with an implementation-grade operator guide:
  - clarified product positioning, architecture map, quick start, local development, quality workflow, API surfaces, and security defaults
  - preserved SSOT reference anchors required by checks (`Where to find X (index)`, `Drift detection`)
  - evidence: README.md :: Where to find X (index)
  - evidence: README.md :: Drift detection
- Updated audit/progress records for the documentation session and regenerated `MANIFEST.sha256`.
  - evidence: AUDIT_REPORT.md :: IMPLEMENTATION_AUDIT (2026-02-07 README_REFRESH)
  - evidence: PROGRESS.md :: Session history
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## v2.2 (focused hardening pass)
- Implemented real worker runtime wiring:
  - added queue runtime orchestration (`ocg worker run|tick|scheduler|stats`)
  - switched Compose workers from `sleep` to live worker process and added dedicated scheduler service
  - evidence: backend/ocg/workers/runtime.py :: def run_worker
  - evidence: docker-compose.yml :: scheduler:
- Added operational indexing migration for hot queries and joins:
  - new Alembic revision `20260208_000002_add_operational_indexes.py`
  - migration test now validates index presence and downgrades to `base`
  - evidence: backend/alembic/versions/20260208_000002_add_operational_indexes.py :: def upgrade
  - evidence: backend/tests/integration/test_migrations.py :: test_alembic_upgrade_and_downgrade
- Expanded observability and correlation:
  - request trace context propagation (`X-Trace-Id`, `traceparent`) and trace-aware error envelopes
  - worker job counters/duration metrics and span instrumentation
  - evidence: backend/ocg/core/observability.py :: class PrometheusMiddleware
  - evidence: backend/ocg/main.py :: http_exception_handler
  - evidence: backend/ocg/workers/jobs.py :: WORKER_JOBS_TOTAL
- Hardened quality gates and CI:
  - `CHECK_PROFILE=ci|full` now strict (no silent missing-tool skips)
  - frontend production build verification added to quality command and CI (Node toolchain setup)
  - evidence: scripts/check.sh :: STRICT_CHECKS
  - evidence: scripts/frontend_check.sh :: frontend_check: pass
  - evidence: .github/workflows/ci.yml :: Setup Node

## v2.3 (frontend security patch)
- Upgraded Next.js from `15.1.2` to patched `15.5.12` and refreshed npm lockfile.
  - evidence: frontend/package.json :: "next": "15.5.12"
  - evidence: frontend/package-lock.json :: "next": "15.5.12"
- Re-ran strict `CHECK_PROFILE=ci` after the upgrade:
  - frontend build, unit/integration tests, migration check, and OpenAPI compatibility pass
  - remaining failure is backend format drift under strict `format` stage
  - evidence: scripts/check.sh :: check profile: ci
