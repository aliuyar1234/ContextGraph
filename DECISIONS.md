# Decisions (append-only)

## D-0001 Primary datastore is PostgreSQL + Alembic
- Decision: Use Postgres 15+ as system-of-record; Alembic for migrations.
- Rationale: Self-hostable, robust indexing, supports JSONB and array fields; fits mid-market scale.
- Verification impact: G-0005.
- Evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Datastore choice

## D-0002 Asynchronous work uses Redis-backed queue with worker pools
- Decision: Use Redis queue for job dispatch and separate queues for bulkheads.
- Rationale: Simple self-host; adequate for target scale; replaceable later.
- Verification impact: G-0004, G-0008.
- Evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Bulkheads

## D-0003 Permission model is fail-closed with UNKNOWN excluded
- Decision: If permissions are unknown, exclude from all user-visible views.
- Rationale: Prevent MNH-1 and reduce risk of leakage.
- Verification impact: G-0001.
- Evidence: spec/03_DOMAIN_MODEL.md :: Permission and privacy invariants

## D-0004 Raw content ingestion is feature-flagged and OFF by default
- Decision: Store metadata-first; raw bodies disabled unless explicitly enabled.
- Rationale: Reduce sensitivity and compliance scope; prevent MNH-3.
- Verification impact: G-0009.
- Evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Retention / purge

## D-0005 Context graph model is stored relationally (patterns/edges/variants)
- Decision: Store context patterns, probabilistic edges, and top variants in relational tables.
- Rationale: Simple operations, indexed queries, rebuildable derived tables.
- Verification impact: G-0003.
- Evidence: spec/03_DOMAIN_MODEL.md :: ContextEdge / ContextPathVariant

## D-0006 Authentication uses OIDC JWT validation
- Decision: Production auth uses OIDC.
- Rationale: Standard enterprise auth; self-host friendly via Keycloak.
- Verification impact: G-0002, G-0011.
- Evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AuthN/AuthZ

## D-0007 Connectors are read-only and MUST reject write scopes
- Decision: No external writes in v1.
- Rationale: Reduce blast radius; aligns with non-goals.
- Verification impact: G-0002.
- Evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Least privilege plan

## D-0008 Multi-queue bulkheads are mandatory
- Decision: Separate queues/pools for connectors vs aggregation vs personal graph.
- Rationale: Prevent MNH-8; predictable degradation.
- Verification impact: G-0004.
- Evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Bulkheads

## D-0009 Observability uses OTel traces + Prometheus metrics
- Decision: Implement OTel instrumentation and Prometheus endpoint.
- Rationale: Standard OSS stack; needed for “telemetry-first” incident response.
- Verification impact: G-0004.
- Evidence: spec/08_OBSERVABILITY.md :: Metrics

## D-0010 LLM tagging is optional and OFF by default
- Decision: Provide plugin interface; default disabled.
- Rationale: Avoid data egress risks; preserve determinism for CI.
- Verification impact: G-0002, G-0009.
- Evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0010

## D-0011 Web UI is Next.js (TypeScript)
- Decision: Use Next.js for dashboards and admin UI.
- Rationale: Fast iteration; strong OSS ecosystem for data viz.
- Verification impact: G-0006.
- Evidence: spec/02_ARCHITECTURE.md :: Component boundary table

## D-0012 API compatibility is enforced via OpenAPI diff gate
- Decision: Track OpenAPI schema and block breaking changes without version bump.
- Rationale: Prevent accidental API breaks.
- Verification impact: G-0012.
- Evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: Versioning + backwards compatibility

## D-0013 Dev-header auth override exists only behind explicit flag
- Decision: `X-Dev-User`/`X-Dev-Role` headers are accepted only when `OCG_DEV_AUTH_ENABLED=true`, while production posture still requires OIDC for non-local bind startup.
- Rationale: Preserve local/operator workflow and deterministic demos without weakening fail-closed startup defaults.
- Verification impact: G-0002, G-0011.
- Evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AuthN/AuthZ (normative)

## D-0014 One-command quality anchor is implemented as Makefile + script runner
- Decision: `make check` delegates to `scripts/check.sh` with `CHECK_PROFILE=fast|ci|full`, and CI calls the same command.
- Rationale: Single command prevents drift between local and CI enforcement.
- Verification impact: G-0006.
- Evidence: spec/10_PHASES_AND_TASKS.md :: T-0002 Define ONE repo-anchoring quality command

## D-0015 Worker runtime is split into queue-consumer and scheduler processes
- Decision: Run a dedicated RQ worker consumer (`ocg worker run`) and a separate scheduler enqueuer (`ocg worker scheduler`) in Compose.
- Rationale: Prevent single-process starvation and make queue health/depth operationally explicit.
- Verification impact: G-0004, G-0008.
- Evidence: spec/02_ARCHITECTURE.md :: Component boundary table (normative)

## D-0016 CI/full profiles are strict and non-skippable
- Decision: `CHECK_PROFILE=ci|full` fails when required toolchains are missing and includes frontend production build verification.
- Rationale: Remove silent pass conditions that masked broken environments and frontend regressions.
- Verification impact: G-0006.
- Evidence: spec/11_QUALITY_GATES.md :: G-0006 CI-ANCHORING gate (maintainability)

## D-0017 Operational indexes are required beyond baseline schema
- Decision: Add explicit secondary indexes for ACL joins, trace hot paths, personal timeline/task reads, and context graph lookup patterns.
- Rationale: Close the gap between normative schema/index expectations and runtime query behavior.
- Verification impact: G-0003, G-0005.
- Evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Schema overview (normative)
