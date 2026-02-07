# SESSION_PROTOCOL.md — Working Session Protocol (Normative)

This protocol applies to any implementation session using this SSOT pack.

## SESSION_START (MUST)
1) Verify integrity:
   - Run the manifest verification procedure.
   - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY
2) Read in required order:
   - evidence: AGENTS.md :: Mandatory session read-order (MUST)
3) Declare intended changes:
   - List which T-IDs you will work on.
   - Identify impacted critical flows (if any):
     - evidence: spec/02_ARCHITECTURE.md :: Main flows (3–7), critical flows marked
4) Apply DSC (Decision Safety Classifier):
   - For each ambiguity, classify:
     - externally constrained?
     - critical flow?
     - unsafe/high-risk?
     - baseline available?
     - safe to decide?
   - If not safe, log as assumption or question and proceed fail-closed.
   - evidence: ASSUMPTIONS.md :: Assumptions (append-only)
   - evidence: QUESTIONS_FOR_USER.md :: Questions for user (non-blocking unless explicitly marked)

## SESSION_END (MUST)
1) Run the quality command and required checks:
   - evidence: spec/10_PHASES_AND_TASKS.md :: T-0002 Define ONE repo-anchoring quality command
2) Update SSOT docs if critical surfaces changed:
   - evidence: spec/11_QUALITY_GATES.md :: G-0007 DOCS-AS-CODE gate (change control)
3) Update DECISIONS/ASSUMPTIONS when structure changed or unknowns were introduced:
   - evidence: DECISIONS.md :: Decisions (append-only)
   - evidence: ASSUMPTIONS.md :: Assumptions (append-only)
4) Update PROGRESS.md with binary evidence pointers for completed tasks:
   - evidence: PROGRESS.md :: Task status table
5) Regenerate MANIFEST.sha256 and update CHANGELOG.md + AUDIT_REPORT.md:
   - evidence: checks/CHECKS_INDEX.md :: CHK-MANIFEST-VERIFY

## QUESTION_ENTRY_FORMAT (MUST)
When adding a question, use:
- Q-ID: stable identifier
- Blocking: YES/NO
- Why it matters: link to critical flow or externally constrained dependency
- Safe default chosen (fail-closed): what will be done until answered
- Where encoded: evidence pointers to the exact spec/decision/assumption sections affected
- What proceeds now: list the tasks that can continue without the answer
