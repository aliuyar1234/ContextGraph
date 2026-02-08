from datetime import UTC

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ocg.connectors.base import Connector, ConnectorEvent, ResourceDelta
from ocg.core.observability import CONNECTOR_FETCH_DURATION, INGEST_EVENTS_TOTAL
from ocg.db import models
from ocg.services.common import utcnow


def _ensure_principal(db: Session, principal_id: str) -> None:
    for pending in db.new:
        if isinstance(pending, models.Principal) and pending.principal_id == principal_id:
            return
    principal = db.get(models.Principal, principal_id)
    if principal:
        return
    principal_type = "group" if principal_id.startswith("group:") else "user"
    db.add(
        models.Principal(
            principal_id=principal_id,
            principal_type=principal_type,
            person_id=principal_id if principal_type == "user" else None,
            external_group_ref=principal_id if principal_type == "group" else None,
            created_at=utcnow(),
        )
    )


def _upsert_resource(db: Session, delta: ResourceDelta) -> models.Resource:
    resource = db.scalar(
        select(models.Resource).where(
            and_(
                models.Resource.tool == delta.tool,
                models.Resource.resource_type == delta.resource_type,
                models.Resource.external_id == delta.external_id,
            )
        )
    )
    now = utcnow()
    if resource is None:
        resource = models.Resource(
            tool=delta.tool,
            resource_type=delta.resource_type,
            external_id=delta.external_id,
            url=delta.url,
            title=delta.title,
            permission_state=delta.permission_state,
            created_at=now,
            updated_at=now,
        )
        db.add(resource)
        db.flush()
    else:
        resource.url = delta.url
        resource.title = delta.title
        resource.permission_state = delta.permission_state
        resource.updated_at = now
    return resource


def _sync_resource_acl(
    db: Session, resource_id: str, principal_ids: list[str], source: str
) -> None:
    for principal_id in principal_ids:
        _ensure_principal(db, principal_id)
        duplicate_pending = any(
            isinstance(pending, models.ResourceACL)
            and pending.resource_id == resource_id
            and pending.principal_id == principal_id
            and pending.revoked_at is None
            for pending in db.new
        )
        if duplicate_pending:
            continue
        existing = db.scalar(
            select(models.ResourceACL).where(
                and_(
                    models.ResourceACL.resource_id == resource_id,
                    models.ResourceACL.principal_id == principal_id,
                    models.ResourceACL.revoked_at.is_(None),
                )
            )
        )
        if not existing:
            db.add(
                models.ResourceACL(
                    resource_id=resource_id,
                    principal_id=principal_id,
                    acl_source=source,
                    granted_at=utcnow(),
                    revoked_at=None,
                )
            )


def ingest_connector_batch(db: Session, connector: Connector, config: dict) -> dict[str, int]:
    connector.validate(config)
    with CONNECTOR_FETCH_DURATION.labels(tool=connector.tool).time():
        events = connector.fetch_events(config)
        resources = connector.fetch_acls(config)

    for acl_delta in resources:
        resource_row = _upsert_resource(db, acl_delta)
        if acl_delta.permission_state == "KNOWN":
            _sync_resource_acl(
                db,
                resource_row.resource_id,
                acl_delta.acl_principal_ids,
                connector.tool,
            )

    raw_written = 0
    traces_written = 0
    for event in events:
        if _raw_exists(db, connector.tool, event.external_event_id):
            continue
        raw_written += 1
        _store_raw_event(db, event)
        normalized, normalized_delta = connector.normalize(event)
        resource_for_trace: models.Resource | None = None
        if normalized_delta:
            resource_for_trace = _upsert_resource(db, normalized_delta)
            if normalized_delta.permission_state == "KNOWN":
                _sync_resource_acl(
                    db,
                    resource_for_trace.resource_id,
                    normalized_delta.acl_principal_ids,
                    connector.tool,
                )

        if not _trace_exists(db, connector.tool, normalized.external_event_id):
            traces_written += 1
            db.add(
                models.TraceEvent(
                    tool=connector.tool,
                    external_event_id=normalized.external_event_id,
                    tool_family=normalized.tool_family,
                    action_type=normalized.action_type,
                    event_time=normalized.event_time.astimezone(UTC),
                    actor_principal_id=normalized.actor_principal_id,
                    resource_id=resource_for_trace.resource_id if resource_for_trace else None,
                    related_resource_ids=[
                        ":".join(ref) for ref in normalized.related_resource_refs
                    ],
                    entity_tags_json=normalized.entity_tags_json,
                    metadata_json=normalized.metadata_json,
                    permission_state=normalized.permission_state,
                )
            )

    db.commit()
    if traces_written:
        INGEST_EVENTS_TOTAL.labels(tool=connector.tool).inc(traces_written)
    return {"raw_event": raw_written, "trace_event": traces_written, "resource_acl": len(resources)}


def _raw_exists(db: Session, tool: str, external_event_id: str) -> bool:
    return (
        db.scalar(
            select(models.RawEvent.raw_event_id).where(
                and_(
                    models.RawEvent.tool == tool,
                    models.RawEvent.external_event_id == external_event_id,
                )
            )
        )
        is not None
    )


def _trace_exists(db: Session, tool: str, external_event_id: str) -> bool:
    return (
        db.scalar(
            select(models.TraceEvent.trace_event_id).where(
                and_(
                    models.TraceEvent.tool == tool,
                    models.TraceEvent.external_event_id == external_event_id,
                )
            )
        )
        is not None
    )


def _store_raw_event(db: Session, event: ConnectorEvent) -> None:
    db.add(
        models.RawEvent(
            tool=event.tool,
            external_event_id=event.external_event_id,
            fetched_at=event.fetched_at,
            payload_json=event.payload_json,
            permission_state=event.permission_state,
        )
    )


def sync_permissions(db: Session, connector: Connector, config: dict) -> dict[str, int]:
    connector.validate(config)
    resources = connector.fetch_acls(config)
    touched = 0
    for delta in resources:
        resource = _upsert_resource(db, delta)
        if delta.permission_state == "KNOWN":
            _sync_resource_acl(db, resource.resource_id, delta.acl_principal_ids, connector.tool)
        touched += 1
    db.commit()
    return {"resources": touched}


def set_connector_enabled(
    db: Session, tool: str, enabled: bool, config: dict
) -> models.ConnectorConfig:
    row = db.scalar(select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool))
    now = utcnow()
    if not row:
        row = models.ConnectorConfig(
            tool=tool,
            enabled=enabled,
            config_json=config,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.config_json = config
        row.updated_at = now
    db.add(
        models.AuditLog(
            actor_principal_id="system",
            action=f"connector_{'enable' if enabled else 'disable'}",
            metadata_json={"tool": tool, "enabled": enabled},
            created_at=now,
        )
    )
    db.commit()
    db.refresh(row)
    return row
