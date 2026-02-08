"""add operational indexes

Revision ID: 20260208_000002
Revises: 20260207_000001
Create Date: 2026-02-08
"""

from alembic import op


revision = "20260208_000002"
down_revision = "20260207_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_connector_config_enabled", "connector_config", ["enabled"], unique=False)
    op.create_index("ix_raw_event_tool_fetched", "raw_event", ["tool", "fetched_at"], unique=False)
    op.create_index(
        "ix_raw_event_permission_state", "raw_event", ["permission_state"], unique=False
    )
    op.create_index("ix_resource_tool_type", "resource", ["tool", "resource_type"], unique=False)
    op.create_index("ix_resource_permission_state", "resource", ["permission_state"], unique=False)
    op.create_index("ix_resource_updated_at", "resource", ["updated_at"], unique=False)
    op.create_index(
        "ix_resource_acl_principal_revoked",
        "resource_acl",
        ["principal_id", "revoked_at"],
        unique=False,
    )
    op.create_index(
        "ix_resource_acl_resource_revoked",
        "resource_acl",
        ["resource_id", "revoked_at"],
        unique=False,
    )
    op.create_index("ix_identity_person_id", "identity", ["person_id"], unique=False)
    op.create_index("ix_principal_person_id", "principal", ["person_id"], unique=False)
    op.create_index("ix_trace_event_event_time", "trace_event", ["event_time"], unique=False)
    op.create_index(
        "ix_trace_event_actor_time",
        "trace_event",
        ["actor_principal_id", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_trace_event_resource_time",
        "trace_event",
        ["resource_id", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_trace_event_tool_action_time",
        "trace_event",
        ["tool_family", "action_type", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_trace_event_permission_state",
        "trace_event",
        ["permission_state"],
        unique=False,
    )
    op.create_index(
        "ix_personal_timeline_person_rank",
        "personal_timeline_item",
        ["person_id", "sequence_rank"],
        unique=False,
    )
    op.create_index(
        "ix_personal_task_person_start",
        "personal_task",
        ["person_id", "start_time"],
        unique=False,
    )
    op.create_index(
        "ix_abstract_trace_process_created",
        "abstract_trace",
        ["process_key", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_abstract_trace_eligible_process",
        "abstract_trace",
        ["eligible", "process_key"],
        unique=False,
    )
    op.create_index(
        "ix_context_pattern_process_pub_updated",
        "context_pattern",
        ["process_key", "published", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_context_edge_pattern_from_prob",
        "context_edge",
        ["pattern_id", "from_step_hash", "probability"],
        unique=False,
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_context_edge_pattern_from_prob", table_name="context_edge")
    op.drop_index("ix_context_pattern_process_pub_updated", table_name="context_pattern")
    op.drop_index("ix_abstract_trace_eligible_process", table_name="abstract_trace")
    op.drop_index("ix_abstract_trace_process_created", table_name="abstract_trace")
    op.drop_index("ix_personal_task_person_start", table_name="personal_task")
    op.drop_index("ix_personal_timeline_person_rank", table_name="personal_timeline_item")
    op.drop_index("ix_trace_event_permission_state", table_name="trace_event")
    op.drop_index("ix_trace_event_tool_action_time", table_name="trace_event")
    op.drop_index("ix_trace_event_resource_time", table_name="trace_event")
    op.drop_index("ix_trace_event_actor_time", table_name="trace_event")
    op.drop_index("ix_trace_event_event_time", table_name="trace_event")
    op.drop_index("ix_principal_person_id", table_name="principal")
    op.drop_index("ix_identity_person_id", table_name="identity")
    op.drop_index("ix_resource_acl_resource_revoked", table_name="resource_acl")
    op.drop_index("ix_resource_acl_principal_revoked", table_name="resource_acl")
    op.drop_index("ix_resource_updated_at", table_name="resource")
    op.drop_index("ix_resource_permission_state", table_name="resource")
    op.drop_index("ix_resource_tool_type", table_name="resource")
    op.drop_index("ix_raw_event_permission_state", table_name="raw_event")
    op.drop_index("ix_raw_event_tool_fetched", table_name="raw_event")
    op.drop_index("ix_connector_config_enabled", table_name="connector_config")
