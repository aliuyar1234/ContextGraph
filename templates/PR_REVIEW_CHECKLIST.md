# PR_REVIEW_CHECKLIST.md (Normative)

**No Evidence, No Accept**

Reviewer MUST require evidence pointers for every checked item.

## Required pre-merge checks (binary)
- Quality command passed in CI (attach CI link and evidence pointers):
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0003 Wire CI (PR blocker) using the same command
  - evidence: spec/11_QUALITY_GATES.md :: G-0006 CI-ANCHORING gate (maintainability)
- Docs-as-Code compliance verified:
  - evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)
- Manifest integrity verified (if SSOT pack changed):
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## Critical-surface change checklist (evidence required)
If the PR changes any of the following, reviewer MUST require updates to the linked SSOT docs:
- API contracts: evidence: spec/04_INTERFACES_AND_CONTRACTS.md :: REST API (normative)
- Data model/migrations/retention: evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: Expand/contract migrations (normative)
- Security boundaries/auth/secrets: evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Trust boundaries (normative)
- Reliability semantics: evidence: spec/07_RELIABILITY_AND_OPERATIONS.md :: Retry rules (normative)
- Observability schema/signals: evidence: spec/08_OBSERVABILITY.md :: Metrics (normative)
- Hot paths/perf budgets: evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)

Evidence fields (reviewer MUST fill):
- Updated SSOT sections (list evidence pointers):
- DECISIONS/ASSUMPTIONS updated (list evidence pointers):
- Gates impacted (list G-IDs with evidence pointers):

## SLOP_BLACKLIST enforcement (SB-0001..SB-0012)
The blacklist is defined in:
- evidence: CONSTITUTION.md :: SLOP_BLACKLIST (SB) — forbidden engineering behaviors

For each SB item, reviewer MUST record evidence that it is satisfied or explicitly exempted by decision.

- SB-0001 evidence:
- SB-0002 evidence:
- SB-0003 evidence:
- SB-0004 evidence:
- SB-0005 evidence:
- SB-0006 evidence:
- SB-0007 evidence:
- SB-0008 evidence:
- SB-0009 evidence:
- SB-0010 evidence:
- SB-0011 evidence:
- SB-0012 evidence:

## Reference integrity (binary)
- All evidence pointers resolve to real files and stable headings/phrases:
  - evidence: checks/CHECKS_INDEX.md :: CHK-REF-INTEGRITY
- No ad-hoc files were added to SSOT pack structure:
  - evidence: checks/CHECKS_INDEX.md :: CHK-NO-ADHOC-FILES
