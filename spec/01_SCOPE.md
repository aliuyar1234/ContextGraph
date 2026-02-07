# Scope — OCG (Open Context Graph)

## In-scope (MUST)
- Ingest event-level activity/change logs from enabled tools into a unified trace schema.
- Maintain canonical entities (users, groups, projects, products, services, customers where available) and relationships.
- Build a per-user personal timeline and task clustering that is visible only to the user by default.
- Produce anonymized abstracted traces that remove raw text and identities.
- Aggregate abstracted traces into k-anonymous patterns and build probabilistic path models (variants + timing/outcomes).
- Expose:
  - Web dashboards (analytics + admin + personal).
  - Read-only REST API.
  - Operator CLI for setup/diagnostics.
- Enforce least privilege:
  - Source ACL ingestion and permission filtering MUST be correct.
  - If ACL is unknown, content MUST NOT be shown in user-facing views.

## Out-of-scope / non-goals (MUST NOT)
- Executing writes to external tools by default (posting messages, updating tickets, merging PRs, CRM updates).
- Full-content document indexing as a first-class capability (raw text OFF by default).
- HR-style employee monitoring or scoring.
- Guaranteed compliance certifications as a deliverable.

## Explicit “will not build” list (MUST NOT)
- Workflow/BPMN engine with hard-coded flows.
- Any mandatory telemetry/phone-home.
- A “super-admin view” of individual personal timelines without explicit user opt-in.

## Target users and roles (RBAC baseline)
- `admin`: configure connectors/auth/retention; view system health; view aggregated analytics.
- `analyst`: view aggregated analytics; NO access to personal timelines of others.
- `user`: view own personal timeline; view aggregated analytics as allowed by org policy config.

Baseline rule: aggregated analytics are “org-level” but MUST still apply data/permission constraints:
- No raw text by default.
- No non-k-anonymous pattern publication.
- No inclusion of restricted resources where ACL cannot be verified.

## Critical flows (mapping to PROJECT_LOCK critical flows; normative)
- CF-1 Connector onboarding + permission sync.
- CF-2 Permission-enforced dashboard queries.
- CF-3 Personal timeline/task clustering (private) + opt-in sharing of abstracted traces.
- CF-4 K-anonymous aggregation and publishing of context graph updates.
- CF-5 Retention/deletion/export workflows.
- CF-6 Suggestion API queries without leakage.

## MVP definition (ship threshold)
MVP MUST include:
- Docker Compose dev deployment.
- OIDC auth (or dev-only local auth mode).
- Postgres schema + migrations.
- 3 connectors enabled end-to-end (Slack, Jira, GitHub) with fail-closed ACL behavior.
- Context graph builder producing:
  - step nodes, probabilistic edges, top-K path variants, timing stats per variant.
- Web UI:
  - Connector health page.
  - Process explorer page (variants + bottlenecks).
  - Personal timeline page (private).
- Read-only API:
  - query process variants and next-step suggestions for a given “process key”.
- Observability + runbook for day-0 and top incidents.
