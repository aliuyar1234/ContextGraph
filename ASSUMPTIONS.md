# Assumptions (append-only)

## A-0001 Default k-anonymity thresholds
- Assumption: Default `k=5` distinct users and `n=20` distinct traces for publishing patterns; configurable.
- Rationale: Conservative privacy baseline for mid-market orgs.
- Verification impact: G-0010.
- Evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules

## A-0002 Initial connector set
- Assumption: MVP ships with Slack, Jira, GitHub connectors.
- Rationale: High coverage for engineering/support workflows.
- Verification impact: G-0004.
- Evidence: spec/01_SCOPE.md :: MVP definition

## A-0003 CI provider baseline
- Assumption: GitHub Actions used as baseline CI, replaceable.
- Rationale: Common for OSS; supports required PR checks.
- Verification impact: G-0006.
- Evidence: spec/10_PHASES_AND_TASKS.md :: T-0003

## A-0004 Deployment is internal by default
- Assumption: Operators deploy behind VPN/reverse proxy; public exposure is rare and must be explicit.
- Rationale: Matches sensitivity tier and fail-closed bind defaults.
- Verification impact: G-0011.
- Evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: Trust boundaries

## A-0005 Titles are optional and default OFF unless enabled
- Assumption: Storing resource titles is configurable; default OFF to reduce sensitivity.
- Rationale: Minimizes data retention risk while allowing “impressive UI” when enabled intentionally.
- Verification impact: G-0009.
- Evidence: spec/05_DATASTORE_AND_MIGRATIONS.md :: resource.title

## A-0006 Target scale fits single Postgres instance
- Assumption: Up to ~1M events/day and ~50 QPS analytics can run on a single Postgres with proper indexing; scale-out is future work.
- Rationale: Aligns with 100–500 employee target.
- Verification impact: G-0003.
- Evidence: spec/00_PROJECT_FINGERPRINT.md :: Fingerprint

## A-0007 No prior engineering constitution existed in chat
- Assumption: A project-specific constitution was generated during packaging to establish normative “HOW”.
- Risk: Rules may not match your internal engineering standards.
- Validation plan: Replace or amend via change process; treat CONSTITUTION.md as normative until superseded.
- Promotion criteria: A dedicated CHANGE_REQUEST introduces an org-approved constitution.
- Verification impact: G-0007, G-0008.
- Evidence: CONSTITUTION.md :: ENGINEERING_POSTER (v1)

## A-0008 Demo profile may use relaxed k-anonymity thresholds in isolated local stacks
- Assumption: Day-0 demo environments can set `k=1,n=1` explicitly to guarantee visible sample patterns without requiring synthetic multi-user volume.
- Risk: Unsafe privacy posture if copied into production configs.
- Validation plan: production/default profiles continue using A-0001 (`k=5,n=20`) unless explicitly changed by operator decision.
- Promotion criteria: richer seeded demo dataset that supports strict defaults without relaxed thresholds.
- Verification impact: G-0010.
- Evidence: spec/03_DOMAIN_MODEL.md :: K-anonymity rules
