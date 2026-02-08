# Datastore & Migrations — OCG (Open Context Graph)

## Datastore choice (normative)
- System of record MUST be PostgreSQL 15+.
  - evidence: DECISIONS.md :: D-0001 Primary datastore is PostgreSQL + Alembic

- Migrations MUST use Alembic with expand/contract discipline.

## Schema overview (normative)
Tables are grouped by layer:
- Ingestion: `connector_config`, `raw_event`
- Canonical resources/traces: `resource`, `resource_acl`, `trace_event`
- Identity/KG: `person`, `identity`, `principal`, `principal_membership`, `kg_entity`, `kg_edge`
- Personal (private): `personal_opt_in`, `personal_timeline_item`, `personal_task`
- Aggregation/context: `abstract_trace`, `context_pattern`, `context_edge`, `context_path_variant`
- Ops: `job_checkpoint`, `audit_log` (no secrets)

### 1) connector_config
- `connector_id` (PK, uuid)
- `tool` (text, not null)
- `enabled` (bool, not null)
- `config_json` (jsonb, not null) — MUST NOT contain plaintext secrets; only secret refs
- `created_at`, `updated_at`
Indexes:
- `(tool)` unique

### 2) raw_event
- `raw_event_id` (PK, uuid)
- `tool` (text, not null)
- `external_event_id` (text, not null)
- `fetched_at` (timestamptz, not null)
- `payload_json` (jsonb, not null) — MAY include metadata; MUST follow redaction policy
- `permission_state` (enum/text, not null)
Constraints:
- unique `(tool, external_event_id)`
Indexes:
- `(tool, fetched_at desc)`
- `(permission_state)`

### 3) resource
- `resource_id` (PK, uuid)
- `tool` (text, not null)
- `resource_type` (text, not null)
- `external_id` (text, not null)
- `url` (text, nullable)
- `title` (text, nullable) — stored only if enabled by config
- `permission_state` (text, not null)
- `created_at`, `updated_at`
Constraints:
- unique `(tool, resource_type, external_id)`
Indexes:
- `(tool, resource_type)`
- `(permission_state)`
- `(updated_at desc)`

### 4) resource_acl
- `resource_id` (uuid, FK->resource, not null)
- `principal_id` (uuid, FK->principal, not null)
- `acl_source` (text, not null)
- `granted_at` (timestamptz, not null)
- `revoked_at` (timestamptz, nullable)
Constraints:
- PK `(resource_id, principal_id, granted_at)`
Indexes:
- `(principal_id, revoked_at)`
- `(resource_id, revoked_at)`
Invariant:
- If a resource has `permission_state=UNKNOWN`, ACL rows are informational only; UI/API MUST still exclude.

### 5) person / identity / principal / principal_membership
person:
- `person_id` (PK, uuid)
- `primary_email` (text, nullable)
- `display_name` (text, nullable)
- `created_at`
identity:
- `identity_id` (PK, uuid)
- `tool` (text)
- `external_user_id` (text)
- `email` (text, nullable)
- `display_name` (text, nullable)
- `person_id` (uuid, FK->person)
- `confidence` (float)
- `created_at`
principal:
- `principal_id` (PK, uuid)
- `principal_type` (text: user|group)
- `person_id` (uuid nullable) — for user principals
- `external_group_ref` (text nullable)
- `created_at`
principal_membership:
- `group_principal_id` (uuid FK->principal)
- `member_principal_id` (uuid FK->principal)
- `created_at`
Indexes:
- `identity(tool, external_user_id)` unique
- `principal(person_id)` where principal_type=user
- `principal_membership(group_principal_id, member_principal_id)` unique

### 6) trace_event
- `trace_event_id` (PK, uuid)
- `tool` (text, not null)
- `external_event_id` (text, not null)
- `tool_family` (text, not null)
- `action_type` (text, not null)
- `event_time` (timestamptz, not null)
- `actor_principal_id` (uuid nullable FK->principal)
- `resource_id` (uuid nullable FK->resource)
- `related_resource_ids` (uuid[] nullable)
- `entity_tags_json` (jsonb not null default `{}`)
- `metadata_json` (jsonb not null default `{}`)
- `permission_state` (text, not null)
Constraints:
- unique `(tool, external_event_id)`
Indexes:
- `(event_time desc)`
- `(actor_principal_id, event_time desc)`
- `(resource_id, event_time desc)`
- GIN on `entity_tags_json` (for process_key derivation)
- `(permission_state)`

### 7) personal_opt_in
- `person_id` (PK uuid FK->person)
- `opt_in_aggregation` (bool not null default false)
- `updated_at`

### 8) personal_timeline_item (private)
- `person_id` (uuid FK->person, not null)
- `trace_event_id` (uuid FK->trace_event, not null)
- `sequence_rank` (bigint not null)
- `created_at`
Constraints:
- PK `(person_id, trace_event_id)`
Indexes:
- `(person_id, sequence_rank)`

### 9) personal_task (private)
- `personal_task_id` (PK uuid)
- `person_id` (uuid FK->person)
- `start_time`, `end_time` (timestamptz)
- `label` (text)
- `confidence` (float)
- `member_trace_event_ids` (uuid[] not null)
Indexes:
- `(person_id, start_time desc)`
- GIN on `member_trace_event_ids`

### 10) abstract_trace
- `abstract_trace_id` (PK uuid)
- `process_key` (text not null)
- `steps_json` (jsonb not null) — list of abstract steps
- `outcome` (text not null)
- `created_at`
- `eligible` (bool not null)
- `source_person_id_hash` (text nullable) — salted hash for distinct user counting ONLY
Constraints:
- `source_person_id_hash` MUST NOT be reversible; salt rotated with retention windows.
Indexes:
- `(process_key, created_at desc)`
- `(eligible)`
- GIN on `steps_json`

### 11) context_pattern
- `pattern_id` (PK uuid)
- `process_key` (text not null)
- `signature` (text not null)
- `distinct_user_count` (int not null)
- `distinct_trace_count` (int not null)
- `published` (bool not null)
- `updated_at`
Indexes:
- `(process_key, published)`
- unique `(process_key, signature)`

### 12) context_edge
- `pattern_id` (uuid FK->context_pattern)
- `from_step_hash` (text)
- `to_step_hash` (text)
- `count` (int)
- `probability` (float)
- `timing_stats_json` (jsonb)
Constraints:
- PK `(pattern_id, from_step_hash, to_step_hash)`
Indexes:
- `(pattern_id, from_step_hash)`

### 13) context_path_variant
- `variant_id` (PK uuid)
- `pattern_id` (uuid FK->context_pattern)
- `rank` (int)
- `step_hashes` (text[])
- `frequency` (float)
- `timing_stats_json` (jsonb)
- `outcome_stats_json` (jsonb)
Indexes:
- `(pattern_id, rank)` unique

## Expand/contract migrations (normative)
- Any schema change MUST follow:
  1) Expand: add nullable columns/new tables/indexes without breaking readers.
  2) Backfill (idempotent job).
  3) Contract: enforce NOT NULL / drop old columns only after all readers updated.
- Rollback:
  - Expand-only migrations MUST be reversible via Alembic downgrade.
  - For data backfills, use idempotent jobs with checkpointing.

## Retention / purge (normative defaults)
- Raw content bodies: OFF by default (not stored).
- Retention windows are configurable; baseline defaults:
  - evidence: spec/00_PROJECT_FINGERPRINT.md :: ## Fingerprint

  - `raw_event`: 30 days
  - `trace_event` + `resource`: 180 days
  - `abstract_trace` + `context_*`: 365 days
  - `logs`: operator-managed
- Purge job MUST:
  - delete eligible rows,
  - vacuum/analyze as needed,
  - recompute derived models if deletions impact aggregates.
- If retention config is missing/invalid, system MUST fail-closed:
  - do not publish new aggregates,
  - continue ingestion only if operator explicitly allows,
  - surface alert in admin UI.

## Implementation status snapshot (2026-02-08)
- Alembic baseline implemented at `backend/alembic/versions/20260207_000001_init.py`.
- Operational index expansion implemented at `backend/alembic/versions/20260208_000002_add_operational_indexes.py` for hot paths and ACL joins.
- CLI migration commands are available via `python -m ocg.cli migrate up|down`.
- Migration validation test exists in `backend/tests/integration/test_migrations.py`.
- Datastore/migration Python modules are aligned with the repository Ruff formatting baseline.
