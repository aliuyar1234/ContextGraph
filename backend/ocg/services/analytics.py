from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ocg.db import models


def list_processes(db: Session) -> list[str]:
    rows = db.scalars(
        select(models.ContextPattern.process_key)
        .where(models.ContextPattern.published.is_(True))
        .distinct()
        .order_by(models.ContextPattern.process_key.asc())
    ).all()
    return list(rows)


def list_patterns(db: Session, process_key: str) -> list[dict]:
    rows = db.scalars(
        select(models.ContextPattern)
        .where(
            and_(
                models.ContextPattern.process_key == process_key,
                models.ContextPattern.published.is_(True),
            )
        )
        .order_by(models.ContextPattern.updated_at.desc())
    ).all()
    return [
        {
            "pattern_id": row.pattern_id,
            "process_key": row.process_key,
            "distinct_user_count": row.distinct_user_count,
            "distinct_trace_count": row.distinct_trace_count,
        }
        for row in rows
    ]


def pattern_variants(db: Session, pattern_id: str) -> list[dict]:
    rows = db.scalars(
        select(models.ContextPathVariant)
        .where(models.ContextPathVariant.pattern_id == pattern_id)
        .order_by(models.ContextPathVariant.rank.asc())
    ).all()
    return [
        {
            "rank": row.rank,
            "frequency": row.frequency,
            "steps": [{"hash": h} for h in row.step_hashes],
            "timing": row.timing_stats_json,
            "outcomes": row.outcome_stats_json,
        }
        for row in rows
    ]


def pattern_edges(db: Session, pattern_id: str) -> list[dict]:
    rows = db.scalars(
        select(models.ContextEdge).where(models.ContextEdge.pattern_id == pattern_id)
    ).all()
    return [
        {
            "from_step_hash": row.from_step_hash,
            "to_step_hash": row.to_step_hash,
            "count": row.count,
            "probability": row.probability,
            "timing": row.timing_stats_json,
        }
        for row in rows
    ]


def bottlenecks(db: Session, pattern_id: str) -> list[dict]:
    rows = db.scalars(
        select(models.ContextEdge).where(models.ContextEdge.pattern_id == pattern_id)
    ).all()
    ranked = sorted(rows, key=lambda edge: edge.timing_stats_json.get("p95_ms", 0), reverse=True)
    return [
        {
            "from_step_hash": row.from_step_hash,
            "to_step_hash": row.to_step_hash,
            "p95_ms": row.timing_stats_json.get("p95_ms", 0),
        }
        for row in ranked[:10]
    ]
