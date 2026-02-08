from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from ocg.core.observability import (
    AGGREGATION_JOB_DURATION,
    ABSTRACT_TRACES_CREATED,
    PATTERNS_DROPPED_K_ANON,
    PATTERNS_PUBLISHED,
)
from ocg.core.settings import Settings
from ocg.db import models
from ocg.services.common import utcnow
from ocg.services.identity import hash_person


def _step_hash(step: dict) -> str:
    material = (
        f"{step['action_type']}|{step['tool_family']}|{','.join(step.get('entity_type_tags', []))}"
    )
    return sha256(material.encode("utf-8")).hexdigest()[:16]


def abstract_opted_in_traces(db: Session) -> int:
    opted_in = {
        row.person_id
        for row in db.scalars(
            select(models.PersonalOptIn).where(models.PersonalOptIn.opt_in_aggregation.is_(True))
        )
    }
    if not opted_in:
        return 0

    db.execute(delete(models.AbstractTrace))
    created = 0
    for person_id in sorted(opted_in):
        tasks = db.scalars(
            select(models.PersonalTask).where(models.PersonalTask.person_id == person_id)
        ).all()
        for task in tasks:
            events = db.scalars(
                select(models.TraceEvent).where(
                    models.TraceEvent.trace_event_id.in_(task.member_trace_event_ids)
                )
            ).all()
            events = sorted(events, key=lambda e: (e.event_time, e.trace_event_id))
            steps = []
            prev_time = None
            for event in events:
                delta = (
                    0
                    if prev_time is None
                    else int((event.event_time - prev_time).total_seconds() * 1000)
                )
                prev_time = event.event_time
                steps.append(
                    {
                        "action_type": event.action_type,
                        "tool_family": event.tool_family,
                        "entity_type_tags": event.entity_tags_json.get("entity_type_tags", []),
                        "process_tags": [f"action:{event.action_type}"],
                        "delta_time_ms_from_prev": min(delta, 86_400_000),
                    }
                )
            process_key = derive_process_key(steps)
            db.add(
                models.AbstractTrace(
                    process_key=process_key,
                    steps_json=steps,
                    outcome=_derive_outcome(task),
                    created_at=utcnow(),
                    eligible=True,
                    source_person_id_hash=hash_person(person_id),
                )
            )
            created += 1
    db.commit()
    if created:
        ABSTRACT_TRACES_CREATED.inc(created)
    return created


def _derive_outcome(task: models.PersonalTask) -> str:
    duration = int((task.end_time - task.start_time).total_seconds())
    return "resolved_fast" if duration < 3600 else "resolved_slow"


def derive_process_key(steps: list[dict]) -> str:
    if not steps:
        return "unknown:empty"
    first = steps[0]
    return f"{first['tool_family']}:action={first['action_type']}"


def cluster_and_publish(db: Session, settings: Settings) -> dict[str, int]:
    with AGGREGATION_JOB_DURATION.time():
        traces = db.scalars(
            select(models.AbstractTrace).where(models.AbstractTrace.eligible.is_(True))
        ).all()
        grouped: dict[tuple[str, str], list[models.AbstractTrace]] = defaultdict(list)
        for trace in traces:
            signature = "->".join([_step_hash(step) for step in trace.steps_json])
            grouped[(trace.process_key, signature)].append(trace)

        db.execute(delete(models.ContextEdge))
        db.execute(delete(models.ContextPathVariant))
        db.execute(delete(models.ContextPattern))
        published = 0
        dropped = 0
        for (process_key, signature), bucket in grouped.items():
            distinct_users = len(
                {trace.source_person_id_hash for trace in bucket if trace.source_person_id_hash}
            )
            distinct_traces = len(bucket)
            publish = (
                distinct_users >= settings.k_anonymity_k
                and distinct_traces >= settings.k_anonymity_n
            )
            pattern = models.ContextPattern(
                process_key=process_key,
                signature=signature,
                distinct_user_count=distinct_users,
                distinct_trace_count=distinct_traces,
                published=publish,
                updated_at=utcnow(),
            )
            db.add(pattern)
            db.flush()
            if publish:
                published += 1
                _build_edges_and_variants(db, pattern.pattern_id, bucket)
            else:
                dropped += 1
        db.commit()
    if published:
        PATTERNS_PUBLISHED.inc(published)
    if dropped:
        PATTERNS_DROPPED_K_ANON.inc(dropped)
    return {"published": published, "dropped": dropped}


def _build_edges_and_variants(
    db: Session, pattern_id: str, traces: list[models.AbstractTrace]
) -> None:
    edge_counter: dict[tuple[str, str], list[int]] = defaultdict(list)
    variant_counter: Counter[tuple[str, ...]] = Counter()
    outcome_counts: Counter[str] = Counter()
    for trace in traces:
        step_hashes = [_step_hash(step) for step in trace.steps_json]
        variant_counter[tuple(step_hashes)] += 1
        outcome_counts[trace.outcome] += 1
        prev_hash = "__START__"
        for step, step_hash in zip(trace.steps_json, step_hashes):
            edge_counter[(prev_hash, step_hash)].append(step.get("delta_time_ms_from_prev", 0))
            prev_hash = step_hash

    outgoing_total: dict[str, int] = defaultdict(int)
    for (frm, _to), samples in edge_counter.items():
        outgoing_total[frm] += len(samples)

    for (frm, to), samples in edge_counter.items():
        count = len(samples)
        db.add(
            models.ContextEdge(
                pattern_id=pattern_id,
                from_step_hash=frm,
                to_step_hash=to,
                count=count,
                probability=count / max(outgoing_total[frm], 1),
                timing_stats_json={
                    "p50_ms": sorted(samples)[len(samples) // 2],
                    "p95_ms": sorted(samples)[max(len(samples) - 1, int(len(samples) * 0.95) - 1)],
                },
            )
        )

    total_variants = sum(variant_counter.values()) or 1
    ranked = sorted(variant_counter.items(), key=lambda item: (-item[1], item[0]))[:10]
    for rank, (variant, count) in enumerate(ranked, start=1):
        db.add(
            models.ContextPathVariant(
                pattern_id=pattern_id,
                rank=rank,
                step_hashes=list(variant),
                frequency=count / total_variants,
                timing_stats_json={},
                outcome_stats_json={
                    key: value / max(sum(outcome_counts.values()), 1)
                    for key, value in outcome_counts.items()
                },
            )
        )


def suggest_next_steps(
    db: Session,
    *,
    process_key: str,
    recent_steps: list[dict],
    limit: int,
) -> list[dict]:
    pattern = db.scalar(
        select(models.ContextPattern).where(
            and_(
                models.ContextPattern.process_key == process_key,
                models.ContextPattern.published.is_(True),
            )
        )
    )
    if not pattern:
        return []
    from_hash = "__START__"
    if recent_steps:
        from_hash = _step_hash(recent_steps[-1])
    edges = db.scalars(
        select(models.ContextEdge)
        .where(
            and_(
                models.ContextEdge.pattern_id == pattern.pattern_id,
                models.ContextEdge.from_step_hash == from_hash,
            )
        )
        .order_by(models.ContextEdge.probability.desc())
    ).all()
    suggestions = []
    for edge in edges[:limit]:
        suggestions.append(
            {
                "step": {"action_type": "unknown", "tool_family": "unknown", "process_tags": []},
                "probability": edge.probability,
                "expected_time_to_next_seconds": int(
                    edge.timing_stats_json.get("p50_ms", 0) / 1000
                ),
            }
        )
    return suggestions
