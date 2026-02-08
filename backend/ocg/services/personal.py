from collections import defaultdict
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ocg.db import models
from ocg.services.common import utcnow
from ocg.services.permissions import PermissionEvaluator


def set_opt_in(db: Session, person_id: str, enabled: bool) -> models.PersonalOptIn:
    row = db.get(models.PersonalOptIn, person_id)
    if row is None:
        row = models.PersonalOptIn(
            person_id=person_id, opt_in_aggregation=enabled, updated_at=utcnow()
        )
        db.add(row)
    else:
        row.opt_in_aggregation = enabled
        row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def build_personal_timeline(db: Session, person_id: str, principal_ids: list[str]) -> int:
    events = db.scalars(
        select(models.TraceEvent).where(models.TraceEvent.actor_principal_id == person_id)
    ).all()
    allowed = [
        event
        for event in events
        if PermissionEvaluator.event_visible_to_principals(
            db, event=event, principal_ids=principal_ids
        )
    ]
    allowed.sort(key=lambda ev: (ev.event_time, ev.trace_event_id))
    db.execute(
        delete(models.PersonalTimelineItem).where(
            models.PersonalTimelineItem.person_id == person_id
        )
    )
    for idx, event in enumerate(allowed, start=1):
        db.add(
            models.PersonalTimelineItem(
                person_id=person_id,
                trace_event_id=event.trace_event_id,
                sequence_rank=idx,
                created_at=utcnow(),
            )
        )
    db.commit()
    return len(allowed)


def cluster_personal_tasks(db: Session, person_id: str) -> int:
    timeline = db.scalars(
        select(models.PersonalTimelineItem)
        .where(models.PersonalTimelineItem.person_id == person_id)
        .order_by(models.PersonalTimelineItem.sequence_rank.asc())
    ).all()
    event_by_id = {
        event.trace_event_id: event
        for event in db.scalars(
            select(models.TraceEvent).where(models.TraceEvent.actor_principal_id == person_id)
        )
    }
    db.execute(delete(models.PersonalTask).where(models.PersonalTask.person_id == person_id))

    tasks: list[list[models.TraceEvent]] = []
    current: list[models.TraceEvent] = []
    last_time = None
    for item in timeline:
        event = event_by_id.get(item.trace_event_id)
        if not event:
            continue
        if last_time and event.event_time - last_time > timedelta(minutes=30) and current:
            tasks.append(current)
            current = []
        current.append(event)
        last_time = event.event_time
    if current:
        tasks.append(current)

    for bucket in tasks:
        action_hist: dict[str, int] = defaultdict(int)
        for ev in bucket:
            action_hist[ev.action_type] += 1
        top_action = sorted(action_hist.items(), key=lambda item: (-item[1], item[0]))[0][0]
        db.add(
            models.PersonalTask(
                person_id=person_id,
                start_time=bucket[0].event_time,
                end_time=bucket[-1].event_time,
                label=f"task:{top_action}",
                confidence=0.8,
                member_trace_event_ids=[ev.trace_event_id for ev in bucket],
            )
        )
    db.commit()
    return len(tasks)


def personal_timeline(
    db: Session, person_id: str, from_iso: str | None, to_iso: str | None
) -> list[dict]:
    query = (
        select(models.PersonalTimelineItem, models.TraceEvent)
        .join(
            models.TraceEvent,
            models.TraceEvent.trace_event_id == models.PersonalTimelineItem.trace_event_id,
        )
        .where(models.PersonalTimelineItem.person_id == person_id)
        .order_by(models.PersonalTimelineItem.sequence_rank.asc())
    )
    rows = db.execute(query).all()
    result = []
    for item, event in rows:
        result.append(
            {
                "trace_event_id": event.trace_event_id,
                "sequence_rank": item.sequence_rank,
                "event_time": event.event_time.isoformat(),
                "action_type": event.action_type,
                "tool_family": event.tool_family,
            }
        )
    return result


def personal_tasks(db: Session, person_id: str) -> list[dict]:
    rows = db.scalars(
        select(models.PersonalTask)
        .where(models.PersonalTask.person_id == person_id)
        .order_by(models.PersonalTask.start_time.desc())
    ).all()
    return [
        {
            "personal_task_id": row.personal_task_id,
            "label": row.label,
            "start_time": row.start_time.isoformat(),
            "end_time": row.end_time.isoformat(),
            "confidence": row.confidence,
        }
        for row in rows
    ]
