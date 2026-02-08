from datetime import timedelta

from ocg.db import models
from ocg.services.common import utcnow
from ocg.services.personal import build_personal_timeline
from ocg.services.permissions import PermissionEvaluator


def _seed_identity(db, person_id: str) -> None:
    db.add(
        models.Person(
            person_id=person_id, primary_email=None, display_name=None, created_at=utcnow()
        )
    )
    db.add(
        models.Principal(
            principal_id=person_id,
            principal_type="user",
            person_id=person_id,
            external_group_ref=None,
            created_at=utcnow(),
        )
    )


def test_permission_unknown_is_excluded(db_session, now):
    _seed_identity(db_session, "u1")
    _seed_identity(db_session, "u2")
    resource = models.Resource(
        tool="jira",
        resource_type="ticket",
        external_id="ENG-1",
        url=None,
        title=None,
        permission_state="UNKNOWN",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(resource)
    db_session.flush()
    event = models.TraceEvent(
        tool="jira",
        external_event_id="evt-1",
        tool_family="tickets",
        action_type="comment",
        event_time=now,
        actor_principal_id="u1",
        resource_id=resource.resource_id,
        related_resource_ids=[],
        entity_tags_json={},
        metadata_json={},
        permission_state="UNKNOWN",
    )
    db_session.add(event)
    db_session.commit()

    visible = PermissionEvaluator.event_visible_to_principals(
        db_session, event=event, principal_ids=["u2"]
    )
    assert visible is False


def test_timeline_sort_is_deterministic(db_session, now):
    _seed_identity(db_session, "u1")
    resource = models.Resource(
        tool="github",
        resource_type="repository",
        external_id="r1",
        url=None,
        title=None,
        permission_state="KNOWN",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(resource)
    db_session.flush()
    db_session.add(
        models.ResourceACL(
            resource_id=resource.resource_id,
            principal_id="u1",
            acl_source="github",
            granted_at=utcnow(),
            revoked_at=None,
        )
    )
    first = models.TraceEvent(
        tool="github",
        external_event_id="a",
        tool_family="code",
        action_type="create",
        event_time=now,
        actor_principal_id="u1",
        resource_id=resource.resource_id,
        related_resource_ids=[],
        entity_tags_json={},
        metadata_json={},
        permission_state="KNOWN",
    )
    second = models.TraceEvent(
        tool="github",
        external_event_id="b",
        tool_family="code",
        action_type="comment",
        event_time=now + timedelta(minutes=1),
        actor_principal_id="u1",
        resource_id=resource.resource_id,
        related_resource_ids=[],
        entity_tags_json={},
        metadata_json={},
        permission_state="KNOWN",
    )
    db_session.add_all([second, first])
    db_session.commit()

    build_personal_timeline(db_session, "u1", ["u1"])
    items = sorted(
        db_session.query(models.PersonalTimelineItem).all(),
        key=lambda item: item.sequence_rank,
    )
    assert [item.trace_event_id for item in items] == [first.trace_event_id, second.trace_event_id]
