# AGENTS.md — SSOT Operating Rules (Highest Precedence)

This file is the highest-precedence instruction set for any AI coding agent or engineer implementing OCG from this pack.

## Precedence order (MUST be applied verbatim)
1) AGENTS.md
2) CONSTITUTION.md
3) spec/* (numeric order; existing files only)
4) DECISIONS.md
5) ASSUMPTIONS.md
6) README.md
7) templates/*, checks/*, runbook content

## Mandatory session read-order (MUST)
Read-order is not precedence; it is the required onboarding path for a working session:
1) README.md
2) AGENTS.md
3) CONSTITUTION.md
4) spec/* (existing files only; numeric order)
5) DECISIONS.md
6) ASSUMPTIONS.md
7) PROGRESS.md
8) QUESTIONS_FOR_USER.md (if present)
9) AUDIT_REPORT.md

## Session protocol (MUST)
Every working session MUST follow:
- evidence: templates/SESSION_PROTOCOL.md :: SESSION_START
- evidence: templates/SESSION_PROTOCOL.md :: SESSION_END

## No silent refactors (MUST)
- Any structural change (API contracts, DB schema, critical flows, trust boundaries, hot paths, gates/checks) MUST:
  - add a DECISIONS.md entry (if it changes “how” or architecture),
  - or add an ASSUMPTIONS.md entry (if it introduces an unknown),
  - update PROGRESS.md,
  - regenerate MANIFEST.sha256.
- Enforcement:
  - evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)
  - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## AGENT_OUTPUT_CONTRACT (AOC) — required structure
Every implementation change set MUST follow this ordered output contract:
1) Plan (T-IDs, what will change, why)
2) Diff (what files will be changed/added; no ad-hoc files)
3) Tests (what will be run, expected pass/fail)
4) Telemetry (what signals prove correctness; which dashboards/metrics/traces)
5) Runbook (what operational steps change, if any)
6) Evidence (evidence pointers proving acceptance criteria and gates passed)
7) Update PROGRESS.md + regenerate MANIFEST.sha256

## No Evidence, No Accept / No Progress (MUST)
- A task is not considered complete until its acceptance criteria are met and evidence pointers are recorded in PROGRESS.md.
- If evidence is missing, status MUST remain not-started or in-progress.

## Critical flow caution (MUST)
Any change touching a critical flow MUST:
- identify impacted CFs:
  - evidence: spec/02_ARCHITECTURE.md :: Main flows (3–7), critical flows marked
- identify impacted abuse cases:
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: TOP_ABUSE_CASES (AC) (>=10; normative)
- update gates/checks if needed:
  - evidence: spec/11_QUALITY_GATES.md :: Gate format
  - evidence: checks/CHECKS_INDEX.md :: Checks overview
