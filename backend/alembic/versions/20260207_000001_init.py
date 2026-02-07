"""initial schema

Revision ID: 20260207_000001
Revises:
Create Date: 2026-02-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260207_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connector_config",
        sa.Column("connector_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("tool", sa.String(64), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "person",
        sa.Column("person_id", sa.String(64), primary_key=True, nullable=False),
        sa.Column("primary_email", sa.String(256), nullable=True),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "principal",
        sa.Column("principal_id", sa.String(64), primary_key=True, nullable=False),
        sa.Column("principal_type", sa.String(32), nullable=False),
        sa.Column("person_id", sa.String(64), sa.ForeignKey("person.person_id"), nullable=True),
        sa.Column("external_group_ref", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "resource",
        sa.Column("resource_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("tool", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(256), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("permission_state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tool", "resource_type", "external_id", name="uq_resource_external_ref"),
    )
    op.create_table(
        "raw_event",
        sa.Column("raw_event_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("tool", sa.String(64), nullable=False),
        sa.Column("external_event_id", sa.String(256), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("permission_state", sa.String(32), nullable=False),
        sa.UniqueConstraint("tool", "external_event_id", name="uq_raw_event_tool_external"),
    )
    op.create_table(
        "identity",
        sa.Column("identity_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("tool", sa.String(64), nullable=False),
        sa.Column("external_user_id", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("person_id", sa.String(64), sa.ForeignKey("person.person_id"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tool", "external_user_id", name="uq_identity_tool_external"),
    )
    op.create_table(
        "principal_membership",
        sa.Column(
            "group_principal_id",
            sa.String(64),
            sa.ForeignKey("principal.principal_id"),
            primary_key=True,
        ),
        sa.Column(
            "member_principal_id",
            sa.String(64),
            sa.ForeignKey("principal.principal_id"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "resource_acl",
        sa.Column(
            "resource_id", sa.String(36), sa.ForeignKey("resource.resource_id"), primary_key=True
        ),
        sa.Column(
            "principal_id", sa.String(64), sa.ForeignKey("principal.principal_id"), primary_key=True
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("acl_source", sa.String(64), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "trace_event",
        sa.Column("trace_event_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("tool", sa.String(64), nullable=False),
        sa.Column("external_event_id", sa.String(256), nullable=False),
        sa.Column("tool_family", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "actor_principal_id", sa.String(64), sa.ForeignKey("principal.principal_id"), nullable=True
        ),
        sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource.resource_id"), nullable=True),
        sa.Column("related_resource_ids", sa.JSON(), nullable=False),
        sa.Column("entity_tags_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("permission_state", sa.String(32), nullable=False),
        sa.UniqueConstraint("tool", "external_event_id", name="uq_trace_event_tool_external"),
    )
    op.create_table(
        "personal_opt_in",
        sa.Column("person_id", sa.String(64), sa.ForeignKey("person.person_id"), primary_key=True),
        sa.Column("opt_in_aggregation", sa.Boolean(), nullable=False, default=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "personal_timeline_item",
        sa.Column("person_id", sa.String(64), sa.ForeignKey("person.person_id"), primary_key=True),
        sa.Column(
            "trace_event_id", sa.String(36), sa.ForeignKey("trace_event.trace_event_id"), primary_key=True
        ),
        sa.Column("sequence_rank", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "personal_task",
        sa.Column("personal_task_id", sa.String(36), primary_key=True),
        sa.Column("person_id", sa.String(64), sa.ForeignKey("person.person_id"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("member_trace_event_ids", sa.JSON(), nullable=False),
    )
    op.create_table(
        "abstract_trace",
        sa.Column("abstract_trace_id", sa.String(36), primary_key=True),
        sa.Column("process_key", sa.String(512), nullable=False),
        sa.Column("steps_json", sa.JSON(), nullable=False),
        sa.Column("outcome", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("source_person_id_hash", sa.String(128), nullable=True),
    )
    op.create_table(
        "context_pattern",
        sa.Column("pattern_id", sa.String(36), primary_key=True),
        sa.Column("process_key", sa.String(512), nullable=False),
        sa.Column("signature", sa.String(512), nullable=False),
        sa.Column("distinct_user_count", sa.Integer(), nullable=False),
        sa.Column("distinct_trace_count", sa.Integer(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("process_key", "signature", name="uq_context_pattern_sig"),
    )
    op.create_table(
        "context_edge",
        sa.Column(
            "pattern_id", sa.String(36), sa.ForeignKey("context_pattern.pattern_id"), primary_key=True
        ),
        sa.Column("from_step_hash", sa.String(128), primary_key=True),
        sa.Column("to_step_hash", sa.String(128), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("timing_stats_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "context_path_variant",
        sa.Column("variant_id", sa.String(36), primary_key=True),
        sa.Column(
            "pattern_id", sa.String(36), sa.ForeignKey("context_pattern.pattern_id"), nullable=False
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("step_hashes", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.Float(), nullable=False),
        sa.Column("timing_stats_json", sa.JSON(), nullable=False),
        sa.Column("outcome_stats_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("pattern_id", "rank", name="uq_context_variant_rank"),
    )
    op.create_table(
        "kg_entity",
        sa.Column("entity_id", sa.String(64), primary_key=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("canonical_key", sa.String(256), nullable=False, unique=True),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("attrs_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "kg_edge",
        sa.Column("edge_id", sa.String(36), primary_key=True),
        sa.Column("src_entity_id", sa.String(64), sa.ForeignKey("kg_entity.entity_id"), nullable=False),
        sa.Column("dst_entity_id", sa.String(64), sa.ForeignKey("kg_entity.entity_id"), nullable=False),
        sa.Column("edge_type", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_trace_event_ids", sa.JSON(), nullable=False),
    )
    op.create_table(
        "job_checkpoint",
        sa.Column("job_name", sa.String(128), primary_key=True),
        sa.Column("checkpoint_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.String(36), primary_key=True),
        sa.Column("actor_principal_id", sa.String(64), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_log",
        "job_checkpoint",
        "kg_edge",
        "kg_entity",
        "context_path_variant",
        "context_edge",
        "context_pattern",
        "abstract_trace",
        "personal_task",
        "personal_timeline_item",
        "personal_opt_in",
        "trace_event",
        "resource_acl",
        "principal_membership",
        "identity",
        "raw_event",
        "resource",
        "principal",
        "person",
        "connector_config",
    ]:
        op.drop_table(table)

