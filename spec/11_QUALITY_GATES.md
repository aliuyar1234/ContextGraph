# Quality Gates — OCG (Open Context Graph)

## Gate format
Each gate includes: why, how-to-verify, pass/fail, evidence pointer.

### G-0001 Permission correctness gate (C1)
- Why: Prevent MNH-1 and MNH-2.
- How-to-verify:
  - Integration test suite runs “permission matrix” scenarios with mocked ACLs.
  - Assert user cannot access unauthorized resources or derived outputs.
- Pass/fail:
  - PASS if all permission tests pass and `permission_state=UNKNOWN` content is excluded.
- Evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: AC-0001
  - evidence: spec/03_DOMAIN_MODEL.md :: Permission and privacy invariants

### G-0002 Security hygiene gate (C2)
- Why: Prevent token leaks and unsafe exposure.
- How-to-verify:
  - Secret scan passes (no secrets in repo).
  - Log redaction scan passes on test logs.
  - Dependency vulnerability scan runs and fails on critical vulnerabilities (operator-tunable allowlist).
- Pass/fail:
  - PASS if no secrets found and redaction scan is clean.
- Evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Secrets handling

### G-0003 Performance regression gate (C3)
- Why: Prevent silent perf decay on HP-0001/HP-0002.
- How-to-verify:
  - Run perf harness against seeded dataset.
  - Compare results to `artifacts/perf/baseline.json`.
- Pass/fail:
  - PASS if no >20% regression in p95/p99 or DB time without an explicit DECISION entry.
- Evidence:
  - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: NON_FUNCTIONAL_BUDGETS

### G-0004 Reliability controls gate (C4)
- Why: Prevent MNH-8 and retry storms.
- How-to-verify:
  - Unit tests assert all external calls set timeouts.
  - Integration tests simulate rate limits and verify bounded retries + circuit breaker opens.
- Pass/fail:
  - PASS if retries bounded and system degrades without crashing.
- Evidence:
  - evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Retry rules

### G-0005 Migration safety gate (C5)
- Why: Prevent schema drift and unsafe upgrades.
- How-to-verify:
  - CI runs `ocg migrate up` on empty DB; runs smoke tests; runs `ocg migrate downgrade` for last expand step where supported.
- Pass/fail:
  - PASS if upgrade succeeds and downgrade works for expand-only steps.
- Evidence:
  - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Expand/contract migrations

### G-0006 CI-ANCHORING gate (maintainability)
- Why: Prevent drift; ensure one command anchors quality.
- How-to-verify:
  - GitHub Actions executes `make check CHECK_PROFILE=ci` as required PR check.
  - `CHECK_PROFILE=ci|full` MUST fail if required tools are missing (no silent bootstrap skips).
- Pass/fail:
  - PASS if required check exists and fails PRs on violations.
- Evidence:
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0002
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0003

### G-0007 DOCS-AS-CODE gate (change control)
- Why: Prevent undocumented changes to critical surfaces.
- How-to-verify:
  - `scripts/docs_guard.sh` checks for changes to OpenAPI/migrations and asserts corresponding spec files and DECISIONS/ASSUMPTIONS are updated.
- Pass/fail:
  - PASS if guard passes.
- Evidence:
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0004

### G-0008 Boundary/coupling fitness gate (architecture erosion)
- Why: Prevent forbidden coupling and dependency reversals.
- How-to-verify:
  - Static check enforces module import rules:
    - UI cannot import backend.
    - Workers cannot import API route layer.
    - Permission evaluator is a single module used everywhere.
- Pass/fail:
  - PASS if dependency linter reports no violations.
- Evidence:
  - evidence: spec/02_ARCHITECTURE.md :: Forbidden coupling

### G-0009 Raw-content default-off gate (C2)
- Why: Prevent MNH-3.
- How-to-verify:
  - Test config with raw-content disabled; assert no DB columns/files store content bodies and API never returns such fields.
- Pass/fail:
  - PASS if raw-content never appears when disabled.
- Evidence:
  - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Retention / purge
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Security posture

### G-0010 K-anonymity enforcement gate (C1/C2)
- Why: Prevent MNH-7 and re-identification.
- How-to-verify:
  - Unit tests for publish thresholds.
  - Integration test seeds traces below thresholds and asserts patterns remain unpublished.
- Pass/fail:
  - PASS if unpublished patterns are not queryable and not shown in UI.
- Evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules

### G-0011 Exposure fail-closed gate (C2/C4)
- Why: Prevent public exposure without auth.
- How-to-verify:
  - Startup test: if bind is non-local and OIDC not configured ⇒ process exits non-zero with clear error.
- Pass/fail:
  - PASS if misconfig fails to start.
- Evidence:
  - evidence: spec/02_ARCHITECTURE.md :: Dependency direction rules

### G-0012 API compatibility gate (C5)
- Why: Prevent accidental breaking changes.
- How-to-verify:
  - CI compares generated OpenAPI schema to previous release baseline and fails on breaking changes unless a version bump is performed and documented.
- Pass/fail:
  - PASS if no breaking changes or version bump + docs exist.
- Evidence:
  - evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: Versioning + backwards compatibility


## QAC Verification Map (normative)
This section makes the Quality Attribute Contract explicit and checkable.

### C1 Correctness
- Invariants (summary): Permission-allowed results; correct aggregation logic.
- Primary gates: G-0001, G-0010.
- Supporting checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-QAC-COVERAGE
  - evidence: checks/CHECKS_INDEX.md :: CHK-REF-INTEGRITY

### C2 Security
- Invariants (summary): Deny-by-default; secrets protected; privacy preserved; raw content default-off.
- Primary gates: G-0002, G-0009, G-0011.
- Supporting checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-FORBIDDEN-TOKEN-LEAK
  - evidence: checks/CHECKS_INDEX.md :: CHK-DOCS-AS-CODE

### C3 Performance
- Invariants (summary): Hot paths regressions prevented.
- Primary gates: G-0003.
- Supporting checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-HP-COVERAGE

### C4 Operability
- Invariants (summary): Observable, bounded retries, safe degradation.
- Primary gates: G-0004, G-0011.
- Supporting checks:
  - evidence: spec/12_RUNBOOK.md :: Top 5 incident playbooks
  - evidence: checks/CHECKS_INDEX.md :: CHK-NFB-PRESENT

### C5 Change
- Invariants (summary): Safe migrations, compatibility discipline, docs-as-code.
- Primary gates: G-0005, G-0006, G-0007, G-0012.
- Supporting checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-DOCS-AS-CODE
  - evidence: checks/CHECKS_INDEX.md :: CHK-REF-INTEGRITY

## SB Enforcement Map (normative)
The slop blacklist is defined in:
- evidence: CONSTITUTION.md :: SLOP_BLACKLIST (SB) — forbidden engineering behaviors

This map ties SB rules to binary enforcement using gates (G-IDs), checks (CHK-IDs), and PR review requirements.

### SB-0001 Unauthorized data exposure
- Enforced by gates: G-0001, G-0002, G-0011.
- Evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: ### AC-0001: Unauthorized user reads restricted resources via analytics

### SB-0002 Bypass privacy boundaries (cross-user personal data)
- Enforced by gates: G-0001, G-0010.
- Evidence:
  - evidence: spec/03_DOMAIN_MODEL.md :: ## Permission and privacy invariants (normative)

### SB-0003 Secrets in repo or logs
- Enforced by gates: G-0002.
- Evidence:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: ## Secrets handling (normative)

### SB-0004 Non-deterministic core outputs
- Enforced by checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-QAC-COVERAGE
- Evidence:
  - evidence: spec/09_TEST_STRATEGY.md :: Determinism expectations (normative)

### SB-0005 Unbounded retries or missing timeouts
- Enforced by gates: G-0004.
- Evidence:
  - evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Retry rules (normative)

### SB-0006 Breaking API changes without versioning
- Enforced by gates: G-0012.
- Evidence:
  - evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: Versioning + backwards compatibility (normative)

### SB-0007 Migration without expand/contract safety
- Enforced by gates: G-0005.
- Evidence:
  - evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Expand/contract migrations (normative)

### SB-0008 Architecture erosion / forbidden coupling
- Enforced by gates: G-0008.
- Evidence:
  - evidence: spec/02_ARCHITECTURE.md :: Forbidden coupling (normative)

### SB-0009 Missing SSOT updates for critical-surface changes
- Enforced by gates: G-0007.
- Evidence:
  - evidence: templates/PR_REVIEW_CHECKLIST.md :: Docs-as-Code compliance verified:

### SB-0010 Missing observability for hot paths
- Enforced by checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-HP-COVERAGE
- Evidence:
  - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)

### SB-0011 Untracked drift (manifest not updated)
- Enforced by checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY
- Evidence:
  - evidence: README.md :: Drift detection

### SB-0012 Ad-hoc files or duplicate SSOT
- Enforced by checks:
  - evidence: checks/CHECKS_INDEX.md :: CHK-NO-ADHOC-FILES
  - evidence: checks/CHECKS_INDEX.md :: CHK-REF-INTEGRITY
