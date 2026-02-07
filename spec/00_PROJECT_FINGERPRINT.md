# OCG (Open Context Graph) — Project Fingerprint (Stage 1 SSOT)

## Canonical summary (1 screen)

### Goals
- Build a self-hosted, open-source system that ingests **enterprise tool activity/change events** and normalizes them into **traces**.
- Build a **knowledge graph** (canonical entities + relationships) to make traces meaningful.
- Build **personal graphs** (private-by-default) that cluster event timelines into tasks/projects.
- Build a **context graph** by aggregating **anonymized abstracted traces** into probabilistic process paths (variants + timing/outcomes), gated by k-anonymity.
- Provide **dashboards + read-only APIs** to explore “how work gets done” and to query likely next steps without leaking sensitive content.

### Non-goals
- No autonomous write-back agents by default (no closing tickets, merging PRs, updating CRM).
- No employee surveillance/productivity scoring.
- No managed SaaS requirement; must run self-hosted.
- No full-text body indexing as a primary feature (metadata-first; raw content optional and OFF by default).
- No hard-coded BPMN/workflow engine.

### Core constraints
- Self-hosted/local deployment (Docker Compose and Kubernetes).
- Permission-aware: MUST enforce source-system access control.
- Privacy-preserving: abstracted traces MUST exclude raw text and identities; aggregation MUST enforce k-anonymity thresholds.
- Open-source distribution; no mandatory telemetry.
- Target org size: ~100–500 employees.

### Must-not-happen failures (from PROJECT_LOCK; normative)
- MNH-1 Unauthorized visibility of entities/traces/dashboards.
- MNH-2 Cross-user leakage from personal graphs without explicit opt-in.
- MNH-3 Raw text stored/displayed when raw ingestion disabled.
- MNH-4 Connector credentials logged plaintext or stored unencrypted.
- MNH-5 Connectors perform external writes without explicit enabling.
- MNH-6 Retention/deletion fails to delete across all stores (incl. embeddings/indexes).
- MNH-7 Aggregation publishes non-k-anonymous patterns (re-identification risk).
- MNH-8 Single connector failure takes down whole system.

## Fingerprint

### Product shape
- Web UI:
  - Admin: connectors, auth, retention, health.
  - Analytics: process/path explorer, variants, bottlenecks, outcomes, “what happens next”.
  - Personal: private timeline + task clusters (visible only to the user).
- Backend:
  - REST API (read-only by default) for entities, traces, context graph queries, suggestions.
  - Background workers for ingestion, normalization, graph building, aggregation.
- CLI:
  - Setup, migrations, connector diagnostics, local dev seed.

### Deployment shape
- Default dev: Docker Compose (single node).
- Production: Kubernetes (stateless app + worker pools; state in Postgres/Redis; optional object store).

### Integrations (initial baseline; configurable; disabled until enabled)
- Slack (events + metadata; message bodies OFF by default)
- Jira (issues, transitions, comments metadata)
- GitHub (PR events, commits metadata, optional deployments)
- Optional: Confluence/Notion metadata (phase-later)

### Sensitivity tier
- Confidential (handles PII + access control metadata + operational traces).

### Runtime model
- Mixed workload:
  - Near-real-time ingest (webhooks where possible) + periodic polling.
  - Batch graph updates on schedules with incremental recompute.
- Fail-closed:
  - Unknown permissions ⇒ exclude from all user-visible outputs.
  - Public network bind without auth ⇒ FAIL TO START.

## Spec Applicability Matrix
- spec/00_PROJECT_FINGERPRINT.md — APPLICABLE: Canonical, used to prevent drift.
- spec/01_SCOPE.md — APPLICABLE: Defines in/out boundaries and critical flows.
- spec/02_ARCHITECTURE.md — APPLICABLE: Defines components, dependency rules, hot paths.
- spec/03_DOMAIN_MODEL.md — APPLICABLE: Defines traces/entities/patterns and invariants.
- spec/04_INTERFACES_AND_CONTRACTS.md — APPLICABLE: Defines APIs/CLI/error/versioning.
- spec/05_DATASTORE_AND_MIGRATIONS.md — APPLICABLE: Postgres schema + retention + migrations.
- spec/06_SECURITY_AND_THREAT_MODEL.md — APPLICABLE: Permission/PII/abuse cases are core.
- spec/07_RELIABILITY_AND_OPERATIONS.md — APPLICABLE: Ingestion + jobs require SRE controls.
- spec/08_OBSERVABILITY.md — APPLICABLE: Must prove correctness + security via telemetry.
- spec/09_TEST_STRATEGY.md — APPLICABLE: Determinism + security/perf regression is required.
- spec/10_PHASES_AND_TASKS.md — APPLICABLE: Provides executable implementation path.
- spec/11_QUALITY_GATES.md — APPLICABLE: Provides enforceable pass/fail checks.
- spec/12_RUNBOOK.md — APPLICABLE: Self-hosted ops needs day-0 and incident playbooks.

## Five Contracts (invariants + risks)

### C1 Correctness Contract
**Invariant:** For any user query, returned objects MUST be permission-allowed and match the requested filters/aggregation logic.  
**Key risks:** stale permission sync; incorrect joins; non-deterministic clustering causing inconsistent dashboards.  
**Mitigations:** permission checks are centralized and tested; unknown-permission objects excluded; deterministic clustering by default.  
**Verification:** G-0001, G-0010.

### C2 Security Contract
**Invariant:** Deny-by-default, least privilege, secrets protected, logs redacted, no raw text storage unless explicitly enabled.  
**Key risks:** token leakage; ACL inference; re-identification via rare patterns.  
**Mitigations:** encrypted secrets, structured log redaction, k-anonymity, rare-pattern suppression.  
**Verification:** G-0002, G-0009, G-0010.

### C3 Performance Contract
**Invariant:** System remains interactive for dashboards and keeps ingestion backlog bounded at target scale.  
**Key risks:** permission joins become slow; aggregation jobs overwhelm DB; N+1 API patterns.  
**Mitigations:** indexed ACL tables, query plans tested, batch jobs bounded, caching for derived aggregates.  
**Verification:** G-0003.

### C4 Operability Contract
**Invariant:** Operators can deploy, observe, and recover without data leaks or undefined behavior.  
**Key risks:** silent connector failures; runaway retries; unbounded storage growth.  
**Mitigations:** health endpoints, backpressure, bounded retries, retention enforcement, runbooks.  
**Verification:** G-0004, G-0008, G-0011.

### C5 Change Contract
**Invariant:** Changes to schema/APIs/critical flows require docs + decision updates; migrations must be expand/contract with rollback.  
**Key risks:** breaking dashboards; schema drift; dependency erosion.  
**Mitigations:** docs-as-code gate; compatibility policy; migration tests; coupling gate.  
**Verification:** G-0005, G-0006, G-0007.

## NON_FUNCTIONAL_BUDGETS (NFB)
If UNKNOWN, budgets are established by harness and baseline capture; regressions require an explicit decision update.

| Dimension | Budget | How measured | Regression rule | Evidence |
|---|---:|---|---|---|
| API read latency p95/p99 | UNKNOWN | `scripts/perf/perf_smoke.py` (Locust or k6) | No >20% regression vs `artifacts/perf/baseline.json` without DECISION | spec/11_QUALITY_GATES.md :: G-0003 |
| Ingestion freshness (event→visible) | UNKNOWN | synthetic event + end-to-end timer | No >20% regression vs baseline | spec/08_OBSERVABILITY.md :: End-to-end SLO |
| Throughput (events/sec) | UNKNOWN | perf harness + worker concurrency sweep | Must sustain target-scale backlog < threshold | spec/07_RELIABILITY_AND_OPERATIONS.md :: Backpressure |
| Error budget (5xx) | UNKNOWN | API metrics | Maintain operator-defined threshold | spec/08_OBSERVABILITY.md :: Golden signals |
| Cost budget | UNKNOWN | operator sizing doc | Must run on “modest infra” (tracked as operator input) | spec/12_RUNBOOK.md :: Sizing |
| Storage growth/day | UNKNOWN | DB size metrics | Must alert and enforce retention | spec/05_DATASTORE_AND_MIGRATIONS.md :: Retention |

## Quality Attribute Profile (intent, risks, invariants, verification)

### Security (rank 1)
- Intent: Prevent unauthorized access; protect secrets; preserve privacy.
- Invariants: deny-by-default; unknown permissions excluded; k-anonymity enforced; secrets encrypted; no raw text by default.
- Verification mapping: G-0002, G-0009, G-0010.

### Reliability (rank 2)
- Intent: Connectors/jobs must degrade gracefully; bounded retries; no global outage from one connector.
- Invariants: bulkheads per connector; idempotent ingestion; bounded queues; dead-letter.
- Verification mapping: G-0004, G-0008.

### Maintainability (rank 3)
- Intent: Prevent architectural erosion and undocumented surface changes.
- Invariants: dependency direction enforced; docs-as-code enforced; typed interfaces.
- Verification mapping: G-0007, G-0008.

### Operability (rank 4)
- Intent: Operators can debug via telemetry-first and runbooks.
- Invariants: structured logs with correlation IDs; OTel traces; dashboards/alerts; safe toggles.
- Verification mapping: G-0004, G-0011.

### Performance (rank 5)
- Intent: Keep dashboards interactive and ingestion bounded at mid-market scale.
- Invariants: indexed permission joins; cached aggregates; perf regression gate.
- Verification mapping: G-0003.

### Compatibility/Upgradability (rank 6)
- Intent: Backwards compatible APIs and safe migrations.
- Invariants: versioned API; deprecation policy; expand/contract migrations.
- Verification mapping: G-0005, G-0012.
