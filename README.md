# Open Context Graph (OCG)

Open Context Graph is a self-hosted, privacy-aware process intelligence platform built from Slack, Jira, and GitHub metadata.  
It combines fail-closed permission enforcement, private personal timelines, and k-anonymous analytics to deliver actionable workflow insight without creating a surveillance system.

## Implementation status (2026-02-08)
- `v2.2` hardening pass completed across worker runtime, CI coverage, migration indexing, tracing, and strict quality checks.
- PHASE tasks `T-0001` through `T-0024` are marked `DONE` with evidence pointers.
- CI is anchored on the same command used locally: `make check CHECK_PROFILE=ci`.

## Core capabilities
- Connector ingestion for Slack, Jira, and GitHub (metadata-first, read-only scopes).
- Identity resolution and knowledge graph entity inference.
- Private user timeline and task clustering.
- Opt-in abstraction and k-anonymous aggregate publication.
- Process explorer analytics with patterns, variants, bottlenecks, and next-step suggestions.
- Admin controls for connector lifecycle and retention configuration.
- OTel-style tracing and Prometheus metrics with Grafana dashboards.

## Architecture at a glance
- `backend/`: FastAPI service, domain logic, CLI, migrations, and worker jobs.
- `frontend/`: Next.js dashboards for admin, analytics, and personal views.
- `ops/`: Prometheus and Grafana configuration for monitoring and alerting.
- `docs/openapi/openapi.v1.json`: API compatibility baseline for gate enforcement.
- `spec/`: normative SSOT specifications and quality gates.

## Quick start (Docker Compose)
Prerequisites:
- Docker + Docker Compose
- Make

Run:
```bash
docker compose up -d postgres redis api workers scheduler ui
docker compose exec api ocg migrate up
docker compose exec api ocg seed demo
curl -f http://127.0.0.1:8080/healthz
curl -f http://127.0.0.1:8080/readyz
```

Open:
- UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8080/docs`

## Local development
Backend:
```bash
python -m pip install -e "backend[dev]"
PYTHONPATH=backend python -m ocg.cli migrate up
PYTHONPATH=backend uvicorn ocg.main:app --host 127.0.0.1 --port 8080 --reload
```

Frontend:
```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

## Quality workflow
- Fast profile: `make check CHECK_PROFILE=fast`
- CI-equivalent: `make check CHECK_PROFILE=ci`
- Full suite: `make check CHECK_PROFILE=full`

The quality command runs format, lint, typecheck, unit tests, profile-gated integration tests, migration checks, secret scans, redaction scans, and (for `ci`/`full`) frontend production build plus OpenAPI compatibility.
- `CHECK_PROFILE=ci|full` is strict: required toolchains/tests cannot silently skip.

Worker operations:
```bash
PYTHONPATH=backend python -m ocg.cli worker run
PYTHONPATH=backend python -m ocg.cli worker scheduler --once
PYTHONPATH=backend python -m ocg.cli worker stats
```

## API surfaces
- Health and metrics:
  - `GET /healthz`
  - `GET /readyz`
  - `GET /metrics`
- Admin:
  - `/api/v1/admin/connectors/*`
- Personal:
  - `/api/v1/personal/timeline`
  - `/api/v1/personal/tasks`
  - `/api/v1/personal/opt_in_aggregation`
- Analytics:
  - `/api/v1/analytics/processes/*`
  - `/api/v1/analytics/patterns/*`
- Suggestions:
  - `POST /api/v1/suggest/next_steps`

## Security and privacy defaults
- Fail-closed permissions: unknown ACL state is excluded from user-visible output.
- OIDC is mandatory for non-local bind startup.
- Raw-content ingestion is disabled by default.
- Aggregated analytics require k-anonymity thresholds.
- Dev header auth override exists only behind explicit flag (`OCG_DEV_AUTH_ENABLED=true`).

## Where to find X (index)
- Goals / constraints / invariants:
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: Canonical summary (1 screen)
- Scope and MVP boundaries:
  - evidence: spec/01_SCOPE.md :: MVP definition (ship threshold)
- Architecture boundaries and critical/hot paths:
  - evidence: spec/02_ARCHITECTURE.md :: Component boundary table (normative)
  - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)
- Domain model and privacy invariants:
  - evidence: spec/03_DOMAIN_MODEL.md :: Permission and privacy invariants (normative)
- REST contracts and compatibility:
  - evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: REST API (normative)
- Datastore schema and migration rules:
  - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Schema overview (normative)
- Security posture, trust boundaries, abuse cases:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Trust boundaries (normative)
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: TOP_ABUSE_CASES (AC) (>=10; normative)
- Reliability semantics:
  - evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Reliability principles (normative)
- Metrics/traces/dashboards:
  - evidence: spec/08_OBSERVABILITY.md :: Signals that prove correctness (contracts C1-C5)
- Deterministic test strategy:
  - evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations (normative)
- Task plan and delivery checkpoints:
  - evidence: spec/10_PHASES_AND_TASKS.md :: PHASE_0_BOOTSTRAP (repo + CI + docs-as-code)
- Quality gates:
  - evidence: spec/11_QUALITY_GATES.md :: Gate format
- Day-0 operations and incidents:
  - evidence: spec/12_RUNBOOK.md :: Top 5 incident playbooks
- Decision and assumption logs:
  - evidence: DECISIONS.md :: Decisions (append-only)
  - evidence: ASSUMPTIONS.md :: Assumptions (append-only)
- Progress and evidence of completion:
  - evidence: PROGRESS.md :: Task status table

## Drift detection
- `MANIFEST.sha256` is the integrity root for this repository.
- Any content change requires:
  1) updating `CHANGELOG.md` and `AUDIT_REPORT.md`,
  2) regenerating `MANIFEST.sha256`,
  3) and verifying integrity.
- Verification reference:
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## Governance
Precedence order (MUST be applied verbatim):
1) AGENTS.md
2) CONSTITUTION.md
3) spec/* (numeric order; existing files only)
4) DECISIONS.md
5) ASSUMPTIONS.md
6) README.md
7) templates/*, checks/*, runbook content
