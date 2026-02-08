from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ocg.db.base import Base


def _uuid() -> str:
    return str(uuid4())


class ConnectorConfig(Base):
    __tablename__ = "connector_config"
    connector_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RawEvent(Base):
    __tablename__ = "raw_event"
    raw_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    permission_state: Mapped[str] = mapped_column(String(32), nullable=False)
    __table_args__ = (
        UniqueConstraint("tool", "external_event_id", name="uq_raw_event_tool_external"),
    )


class Resource(Base):
    __tablename__ = "resource"
    resource_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    permission_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("tool", "resource_type", "external_id", name="uq_resource_external_ref"),
    )


class Person(Base):
    __tablename__ = "person"
    person_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    primary_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Identity(Base):
    __tablename__ = "identity"
    identity_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    external_user_id: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.person_id"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("tool", "external_user_id", name="uq_identity_tool_external"),
    )


class Principal(Base):
    __tablename__ = "principal"
    principal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    principal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    person_id: Mapped[str | None] = mapped_column(ForeignKey("person.person_id"), nullable=True)
    external_group_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PrincipalMembership(Base):
    __tablename__ = "principal_membership"
    group_principal_id: Mapped[str] = mapped_column(
        ForeignKey("principal.principal_id"), primary_key=True
    )
    member_principal_id: Mapped[str] = mapped_column(
        ForeignKey("principal.principal_id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResourceACL(Base):
    __tablename__ = "resource_acl"
    resource_id: Mapped[str] = mapped_column(ForeignKey("resource.resource_id"), primary_key=True)
    principal_id: Mapped[str] = mapped_column(
        ForeignKey("principal.principal_id"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    acl_source: Mapped[str] = mapped_column(String(64), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TraceEvent(Base):
    __tablename__ = "trace_event"
    trace_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    tool_family: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_principal_id: Mapped[str | None] = mapped_column(
        ForeignKey("principal.principal_id"), nullable=True
    )
    resource_id: Mapped[str | None] = mapped_column(
        ForeignKey("resource.resource_id"), nullable=True
    )
    related_resource_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    entity_tags_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    permission_state: Mapped[str] = mapped_column(String(32), nullable=False)
    __table_args__ = (
        UniqueConstraint("tool", "external_event_id", name="uq_trace_event_tool_external"),
    )


class PersonalOptIn(Base):
    __tablename__ = "personal_opt_in"
    person_id: Mapped[str] = mapped_column(ForeignKey("person.person_id"), primary_key=True)
    opt_in_aggregation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PersonalTimelineItem(Base):
    __tablename__ = "personal_timeline_item"
    person_id: Mapped[str] = mapped_column(ForeignKey("person.person_id"), primary_key=True)
    trace_event_id: Mapped[str] = mapped_column(
        ForeignKey("trace_event.trace_event_id"), primary_key=True
    )
    sequence_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PersonalTask(Base):
    __tablename__ = "personal_task"
    personal_task_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.person_id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    member_trace_event_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class AbstractTrace(Base):
    __tablename__ = "abstract_trace"
    abstract_trace_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    process_key: Mapped[str] = mapped_column(String(512), nullable=False)
    steps_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    outcome: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_person_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ContextPattern(Base):
    __tablename__ = "context_pattern"
    pattern_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    process_key: Mapped[str] = mapped_column(String(512), nullable=False)
    signature: Mapped[str] = mapped_column(String(512), nullable=False)
    distinct_user_count: Mapped[int] = mapped_column(Integer, nullable=False)
    distinct_trace_count: Mapped[int] = mapped_column(Integer, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("process_key", "signature", name="uq_context_pattern_sig"),)


class ContextEdge(Base):
    __tablename__ = "context_edge"
    pattern_id: Mapped[str] = mapped_column(
        ForeignKey("context_pattern.pattern_id"), primary_key=True
    )
    from_step_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    to_step_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    timing_stats_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ContextPathVariant(Base):
    __tablename__ = "context_path_variant"
    variant_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pattern_id: Mapped[str] = mapped_column(
        ForeignKey("context_pattern.pattern_id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    step_hashes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    frequency: Mapped[float] = mapped_column(Float, nullable=False)
    timing_stats_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    outcome_stats_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    __table_args__ = (UniqueConstraint("pattern_id", "rank", name="uq_context_variant_rank"),)


class KGEntity(Base):
    __tablename__ = "kg_entity"
    entity_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_key: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    attrs_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class KGEdge(Base):
    __tablename__ = "kg_edge"
    edge_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    src_entity_id: Mapped[str] = mapped_column(ForeignKey("kg_entity.entity_id"), nullable=False)
    dst_entity_id: Mapped[str] = mapped_column(ForeignKey("kg_entity.entity_id"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_trace_event_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class JobCheckpoint(Base):
    __tablename__ = "job_checkpoint"
    job_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    checkpoint_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"
    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
