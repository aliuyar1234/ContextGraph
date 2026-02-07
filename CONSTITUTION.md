# CONSTITUTION.md — Engineering Constitution (project-tailored)

## ENGINEERING_POSTER (v1)
**Purpose:** Make implementation deterministic, fail-closed, and secure for a self-hosted context-graph product.

### Prime directives (MUST)
1) **Fail-closed by default.**
   - Unknown permission ⇒ exclude from user-visible outputs.
   - Public network bind without auth ⇒ fail to start.
   - evidence: spec/02_ARCHITECTURE.md :: Dependency direction rules (normative)
   - evidence: spec/03_DOMAIN_MODEL.md :: Permission and privacy invariants (normative)

2) **Least privilege everywhere.**
   - Read-only external connector scopes.
   - Separate DB roles by component.
   - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Least privilege plan (normative)

3) **Privacy-by-design.**
   - Personal graph is user-scoped; no admin override by default.
   - Aggregates must be k-anonymous; rare patterns suppressed.
   - evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules (normative)
   - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0002: Admin views personal timelines of employees (surveillance)

4) **Contracts are SSOT.**
   - API, schema, and critical flow semantics are defined only in SSOT docs.
   - Any change must update SSOT and the decision log.
   - evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)

5) **Determinism beats cleverness.**
   - Core pipelines must be deterministic under fixed inputs.
   - Optional ML/LLM features must be explicitly enabled and auditable.
   - evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations (normative)
   - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0010: LLM plugin leaks data externally

6) **Observability is part of correctness.**
   - Hot paths must have traces and golden-signal metrics.
   - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)
   - evidence: spec/08_OBSERVABILITY.md :: Signals that prove correctness (contracts C1–C5)

### Five Contracts (C1–C5) (normative statement)
The project’s contracts are defined in:
- evidence: spec/00_PROJECT_FINGERPRINT.md :: Five Contracts (invariants + risks)

Implementation MUST satisfy gates mapped to these contracts:
- evidence: spec/11_QUALITY_GATES.md :: QAC Verification Map (normative)

## SLOP_BLACKLIST (SB) — forbidden engineering behaviors
Each SB item includes:
- Detect: what flags the violation
- Remediate: how to fix
- Enforce: what must block merges

### SB-0001 Unauthorized visibility paths
- Detect: G-0001 and G-0011 failures.
- Remediate: fix permission joins; ensure unknown-permission exclusion; add regression tests.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0001 Permission correctness gate (C1)

### SB-0002 Cross-user personal data access
- Detect: permission tests and personal endpoint authorization tests.
- Remediate: enforce `caller_person_id == requested_person_id`; remove any bypass.
- Enforce: evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0002: Admin views personal timelines of employees (surveillance)

### SB-0003 Secrets leakage (repo, logs, configs)
- Detect: security hygiene gate; log redaction scan.
- Remediate: move to secret refs; scrub logs; rotate compromised tokens.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0002 Security hygiene gate (C2)

### SB-0004 Non-deterministic core outputs
- Detect: determinism tests fail (timeline ordering, clustering stability).
- Remediate: enforce stable ordering keys; seed any stochastic components; prefer heuristics.
- Enforce: evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations (normative)

### SB-0005 Missing timeouts or unbounded retries
- Detect: reliability controls tests (timeouts asserted; retry storm simulation).
- Remediate: add timeouts; bound retries; add circuit breakers/bulkheads.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0004 Reliability controls gate (C4)

### SB-0006 Breaking public contracts silently
- Detect: OpenAPI diff gate failure.
- Remediate: add backwards compatible fields only, or bump API version and document migration.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0012 API compatibility gate (C5)

### SB-0007 Unsafe schema migrations
- Detect: migration safety gate failure.
- Remediate: apply expand/contract; add idempotent backfills; ensure rollback safety.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0005 Migration safety gate (C5)

### SB-0008 Architecture erosion and forbidden coupling
- Detect: boundary/coupling fitness gate failure.
- Remediate: restore dependency direction; isolate permission evaluator module; remove cross-layer imports.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0008 Boundary/coupling fitness gate (architecture erosion)

### SB-0009 Critical changes without SSOT updates
- Detect: docs-as-code gate failure; PR checklist missing evidence pointers.
- Remediate: update relevant spec sections; add decision entry; update runbook if operational behavior changed.
- Enforce: evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)

### SB-0010 Hot paths without traces/metrics
- Detect: missing required spans/metrics for hot path endpoints.
- Remediate: add OTel spans and golden signals; update dashboards/alerts.
- Enforce: evidence: spec/08_OBSERVABILITY.md :: Traces (normative)

### SB-0011 Drift: pack changed without manifest regen
- Detect: manifest verify check fails.
- Remediate: regenerate MANIFEST.sha256 and update CHANGELOG.md and AUDIT_REPORT.md.
- Enforce: evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

### SB-0012 SSOT sprawl (ad-hoc files or duplicated sources of truth)
- Detect: no-ad-hoc-files check fails; reference integrity check fails.
- Remediate: move content into canonical homes and reference with evidence pointers.
- Enforce: evidence: checks/CHECKS_INDEX.md :: CHK-NO-ADHOC-FILES

## Exception process (MUST)
If violating any SB rule is necessary:
1) Add a DECISIONS.md entry describing:
   - the exception,
   - blast radius,
   - mitigation plan,
   - and how it will be enforced and measured.
   - evidence: DECISIONS.md :: Decisions (append-only)
2) Update gates/checks to prevent silent repetition of the exception.
   - evidence: checks/CHECKS_INDEX.md :: Checks overview
3) Record operational impact in the runbook if applicable.
   - evidence: spec/12_RUNBOOK.md :: Operational toggles (feature flags) with safe defaults
4) Regenerate MANIFEST.sha256 and update CHANGELOG.md and AUDIT_REPORT.md.
   - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY
