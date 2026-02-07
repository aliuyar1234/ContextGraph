# Domain Model — OCG (Open Context Graph)

## Core concepts
OCG models:
- **Resources** (enterprise entities): docs, tickets, PRs, channels, repos, incidents, deals (metadata-first).
- **Trace events**: normalized action/change records with timestamps and references to resources and actors.
- **Knowledge graph (KG)**: canonical entities and relationships inferred from resources + traces.
- **Personal graph**: per-user timeline and clustered tasks (private-by-default).
- **Abstract traces**: anonymized, coarse step sequences derived from personal traces.
- **Context graph**: aggregated probabilistic process paths derived from abstract traces.

## Canonical enumerations (normative)
### Tool family
- `docs`, `chat`, `tickets`, `code`, `crm`, `calendar`, `dashboards`, `internal`, `unknown`

### Action type
- `create`, `view`, `edit`, `comment`, `share`, `assign`, `status_change`, `escalate`, `approve`, `merge`, `deploy`, `resolve`, `message`, `link`, `unlink`, `unknown`

### Permission state
- `KNOWN`, `UNKNOWN`, `INHERITED_UNKNOWN`

## Entity types (KG baseline)
- `Person`, `Team`, `Project`, `Product`, `Service`, `Customer`, `Incident`, `Deal`, `Repository`, `Document`, `Ticket`, `Channel`

## Key domain objects (fields are conceptual; storage in spec/05)

### Identity
- Purpose: reconcile users across tools.
- Fields: `identity_id`, `tool`, `external_user_id`, `email`, `display_name`, `canonical_person_id`, `confidence`, `created_at`.

### Principal
- Purpose: authorization unit used for permission evaluation.
- Types: `user`, `group`.
- Fields: `principal_id`, `principal_type`, `canonical_person_id` (if user), `external_group_ref` (if group), `created_at`.

### Resource
- Purpose: any external object referenced by traces.
- Fields: `resource_id`, `tool`, `resource_type`, `external_id`, `url`, `title` (optional; may be disabled), `created_at`, `updated_at`, `permission_state`.

### ResourceACL
- Purpose: store allowlist of principals.
- Fields: `resource_id`, `principal_id`, `acl_source` (tool), `granted_at`, `revoked_at` (nullable).
- Invariant: absence of ACL with `permission_state=KNOWN` MAY mean “public within org” only if tool semantics confirm; otherwise treat as restricted.

### TraceEvent (normalized)
- Purpose: canonical record of an action/change.
- Fields:
  - `trace_event_id` (stable)
  - `tool`, `tool_family`
  - `action_type`
  - `event_time`
  - `actor_principal_id` (nullable; if unknown actor)
  - `resource_id` (nullable if event not tied to a resource)
  - `related_resource_ids[]` (links)
  - `entity_tags` (derived KG entity references: `product_id`, `service_id`, `incident_id`, etc.)
  - `metadata` (JSON; MUST be schema-validated per tool mapping)
  - `permission_state` (mirrors resource; if unknown ⇒ exclude from user-facing)

### KnowledgeEntity / KnowledgeEdge
- Purpose: represent KG nodes/edges for canonical rollups.
- Fields (node): `entity_id`, `entity_type`, `canonical_key`, `display_name`, `confidence`, `attrs_json`.
- Fields (edge): `edge_id`, `src_entity_id`, `dst_entity_id`, `edge_type`, `confidence`, `evidence_trace_event_ids[]`.

### PersonalTimelineItem
- Purpose: user-scoped view of trace events ordered and enriched.
- Fields: `person_id`, `trace_event_id`, `sequence_rank`, `enriched_tags`, `created_at`.
- Invariant: accessible only to the same authenticated user.

### PersonalTask
- Purpose: cluster timeline items into semantic tasks/projects.
- Fields: `personal_task_id`, `person_id`, `start_time`, `end_time`, `label` (heuristic/LLM), `confidence`, `member_trace_event_ids[]`.
- Invariant: task labels MUST NOT include raw text from content bodies unless raw-content feature is enabled.

### AbstractTrace
- Purpose: anonymized sequence used for aggregation.
- Fields:
  - `abstract_trace_id`
  - `source_scope` (org deployment ID)
  - `process_key` (derived key, e.g., `incident:service=S:severity=P1` or `sales:segment=MM`)
  - `steps[]` where each step includes:
    - `action_type`, `tool_family`
    - `entity_type_tags[]` (e.g., `Incident`, `Ticket`, `Document`)
    - `process_tags[]` (e.g., `investigate_alert`, `draft_spec`) — derived
    - `delta_time_ms_from_prev` (bucketed)
  - `outcome` (bucketed: `resolved_fast`, `resolved_slow`, `closed_won`, `unknown`)
  - `eligibility_flags` (k-anon eligible? user opted-in? permission-known-only?)
- Invariant: MUST NOT include actor identifiers, raw text, resource URLs, or external IDs.

### ContextPattern (cluster)
- Purpose: group of similar abstract traces representing one process “theme”.
- Fields: `pattern_id`, `process_key`, `signature`, `distinct_user_count`, `distinct_trace_count`, `published` (bool).
- Invariant: `published` MUST be false unless k-anonymity thresholds satisfied.

### ContextEdge (probabilistic next-step model)
- Purpose: represent transitions between steps for a pattern.
- Fields: `pattern_id`, `from_step_hash`, `to_step_hash`, `count`, `probability`, `timing_stats`.
- Invariant: probabilities MUST sum to 1.0 (±epsilon) for outgoing edges per `(pattern_id, from_step_hash)`.

### ContextPathVariant
- Purpose: store top-K most frequent step sequences.
- Fields: `variant_id`, `pattern_id`, `rank`, `step_hashes[]`, `frequency`, `timing_stats`, `outcome_stats`.
- Invariant: only derived from published patterns.

## K-anonymity rules (normative)
- A pattern MAY be published only if:
  - `distinct_user_count >= k` AND `distinct_trace_count >= n`
  - evidence: spec/06_SECURITY_AND_THREAT_MODEL.md :: ### AC-0004: Pattern re-identification via rare traces
- `k` and `n` MUST be configurable.
- Default thresholds are defined as assumptions.
  - evidence: ASSUMPTIONS.md :: A-0001 Default k-anonymity thresholds


## Permission and privacy invariants (normative)
- Any user-visible view derived from resources/traces MUST exclude records with `permission_state != KNOWN`.
- Personal graphs MUST be user-scoped; no cross-user reads.
- Aggregation MUST operate only on opted-in users’ abstracted traces (opt-in is explicit and revocable).
- Aggregated dashboards MUST only show published patterns (k-anonymous).
