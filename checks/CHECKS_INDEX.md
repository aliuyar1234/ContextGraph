# CHECKS_INDEX.md — Pack Checks (Normative)

## Checks overview
Checks (CHK-IDs) are the binary enforcement layer that makes the SSOT pack drift-resistant. A check is either:
- automated (intended to be implemented as scripts in the repo), or
- manual (review procedure with explicit pass/fail criteria).

Canonical homes:
- Gates (G-IDs): evidence: spec/11_QUALITY_GATES.md :: Gate format
- PR enforcement: evidence: templates/PR_REVIEW_CHECKLIST.md :: Required pre-merge checks (binary)

## CHK-MANIFEST-VERIFY
- Purpose: Detect drift. The manifest is the integrity root for the SSOT pack.
- Type: automated or manual
- How to run:
  - Recompute sha256 for every file except MANIFEST.sha256, sort paths lexicographically, and compare lines.
- Pass/fail:
  - PASS if computed manifest exactly matches MANIFEST.sha256.
- Evidence location:
  - evidence: MANIFEST.sha256 :: AGENTS.md

## CHK-CORE-FILES
- Purpose: Ensure canonical SSOT structure exists.
- Type: automated
- How to run:
  - Verify all required root/spec/templates/checks files exist and no extra folders exist.
- Pass/fail:
  - PASS if structure matches the canonical tree and contains no unexpected paths.
- Evidence location:
  - evidence: AUDIT_REPORT.md :: Pack structure audit

## CHK-FINGERPRINT-MATRIX
- Purpose: Enforce matrix ↔ filesystem consistency.
- Type: automated
- How to run:
  - Parse the Spec Applicability Matrix and verify every APPLICABLE spec file exists and no NON-APPLICABLE spec file exists.
- Pass/fail:
  - PASS if matrix and filesystem match exactly.
- Evidence location:
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: Spec Applicability Matrix

## CHK-EVIDENCE-POINTER-FORMAT
- Purpose: Enforce consistent, searchable evidence pointers.
- Type: automated
- How to run:
  - Find all evidence-pointer lines and validate syntax shape: `relative_path :: heading-or-unique-phrase`.
  - Validate that `relative_path` exists in the ZIP.
  - Validate that `heading-or-unique-phrase` occurs as an exact substring in the referenced file.
- Pass/fail:
  - PASS if all evidence pointers conform.
- Evidence location:
  - evidence: README.md :: Where to find X (index)

## CHK-REF-INTEGRITY
- Purpose: Ensure all references resolve (no dead pointers).
- Type: automated + manual spot-check
- How to run:
  - For each evidence pointer, verify the file exists.
  - For each `:: phrase`, verify it appears in the referenced file.
- Pass/fail:
  - PASS if all evidence pointers resolve to an existing file and phrase.
- Evidence location:
  - evidence: AUDIT_REPORT.md :: Reference integrity audit

## CHK-NO-ADHOC-FILES
- Purpose: Prevent SSOT sprawl.
- Type: automated
- How to run:
  - List all ZIP paths and compare to canonical tree.
- Pass/fail:
  - PASS if no paths exist outside canonical tree.
- Evidence location:
  - evidence: AUDIT_REPORT.md :: Pack structure audit

## CHK-QAC-COVERAGE
- Purpose: Ensure every contract is gated.
- Type: automated
- How to run:
  - Confirm C1–C5 are present and mapped to G-IDs, and those G-IDs exist.
- Pass/fail:
  - PASS if mapping exists and all referenced gates exist.
- Evidence location:
  - evidence: spec/11_QUALITY_GATES.md :: QAC Verification Map (normative)

## CHK-NFB-PRESENT
- Purpose: Ensure non-functional budgets exist.
- Type: automated
- How to run:
  - Verify NFB table exists and contains a harness + regression rule for unknown values.
- Pass/fail:
  - PASS if table exists and is non-thin.
- Evidence location:
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: NON_FUNCTIONAL_BUDGETS (NFB)

## CHK-HP-COVERAGE
- Purpose: Ensure declared hot paths have performance gates and tracing spans.
- Type: automated
- How to run:
  - Verify HP entries exist and each maps to at least one performance gate.
- Pass/fail:
  - PASS if each HP maps to a gate and includes required tracing spans.
- Evidence location:
  - evidence: spec/02_ARCHITECTURE.md :: HOT_PATHS (HP) (normative)

## CHK-TB-EXISTS
- Purpose: Ensure trust boundaries are explicitly documented.
- Type: automated
- How to run:
  - Verify a trust boundary diagram exists.
- Pass/fail:
  - PASS if trust boundary section exists.
- Evidence location:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Trust boundaries (normative)

## CHK-ABUSE-CASES-10
- Purpose: Ensure threat modeling is non-thin.
- Type: automated
- How to run:
  - Count abuse cases AC-0001.. and verify at least 10 exist.
- Pass/fail:
  - PASS if >= 10 abuse cases are present.
- Evidence location:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: TOP_ABUSE_CASES (AC) (>=10; normative)

## CHK-CI-ANCHORING
- Purpose: Ensure a single quality command is anchored locally and in CI.
- Type: manual (until repo exists), then automated
- How to run:
  - Confirm spec/10 defines the quality command task and CI wiring task, and spec/11 has CI-ANCHORING gate.
- Pass/fail:
  - PASS if all required tasks and the gate exist.
- Evidence location:
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0002 Define ONE repo-anchoring quality command
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0003 Wire CI (PR blocker) using the same command
  - evidence: spec/11_QUALITY_GATES.md :: G-0006 CI-ANCHORING gate (maintainability)

## CHK-DOCS-AS-CODE
- Purpose: Prevent undocumented changes to critical surfaces.
- Type: manual + automated guard (once implemented)
- How to run:
  - Confirm docs guard task exists and docs-as-code gate exists.
  - Confirm PR review checklist contains evidence fields.
- Pass/fail:
  - PASS if enforcement exists and is referenced as a PR blocker.
- Evidence location:
  - evidence: spec/10_PHASES_AND_TASKS.md :: T-0004 Docs-as-code enforcement guard
  - evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)
  - evidence: templates/PR_REVIEW_CHECKLIST.md :: Critical-surface change checklist (evidence required)

## CHK-SLOP-MAPPING
- Purpose: Ensure SB rules are mapped to enforcement.
- Type: manual
- How to run:
  - Confirm SB list exists and each SB maps to at least one gate/check/checklist entry.
- Pass/fail:
  - PASS if SB-0001..SB-0012 mapping is present.
- Evidence location:
  - evidence: CONSTITUTION.md :: SLOP_BLACKLIST (SB) — forbidden engineering behaviors
  - evidence: spec/11_QUALITY_GATES.md :: SB Enforcement Map (normative)

## CHK-FORBIDDEN-TERMS
- Purpose: Ensure forbidden placeholder tokens appear only in this section.
- Type: automated
- How to run:
  - Scan all files and verify that the forbidden token literals appear only in this section.
- Pass/fail:
  - PASS if forbidden tokens appear only here.
- Evidence location:
  - evidence: checks/CHECKS_INDEX.md :: CHK-FORBIDDEN-TERMS

Forbidden token literals (must appear only here):
- TODO
- TBD
- FIXME
- XXX
- PLACEHOLDER
- ???
- <FILL>

## CHK-FORBIDDEN-TOKEN-LEAK
- Purpose: Ensure no forbidden token literals appear outside CHK-FORBIDDEN-TERMS.
- Type: automated
- How to run:
  - Use the forbidden token list in CHK-FORBIDDEN-TERMS and scan all files except CHECKS_INDEX.md.
  - Scan CHECKS_INDEX.md and ensure forbidden tokens appear only within the CHK-FORBIDDEN-TERMS section.
- Pass/fail:
  - PASS if no leaks are found.
- Evidence location:
  - evidence: AUDIT_REPORT.md :: Forbidden token leak audit
