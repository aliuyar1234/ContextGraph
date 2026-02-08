from __future__ import annotations

import time

from redis import Redis
from rq import Queue, Worker
from sqlalchemy import select

from ocg.core.observability import INGEST_BACKLOG_DEPTH
from ocg.core.settings import get_settings
from ocg.db import models
from ocg.db.session import SessionLocal
from ocg.workers import jobs
from ocg.workers.queues import (
    AGGREGATE_CONTEXT_QUEUE,
    ALL_QUEUES,
    CONNECTOR_INGEST_QUEUE,
    NORMALIZE_QUEUE,
    PERMISSIONS_SYNC_QUEUE,
)


def parse_queue_names(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return list(ALL_QUEUES)

    if isinstance(raw, str):
        candidates = [part.strip() for part in raw.split(",")]
    else:
        candidates = [part.strip() for part in raw]

    selected: list[str] = []
    for name in candidates:
        if not name:
            continue
        if name not in ALL_QUEUES:
            allowed = ", ".join(ALL_QUEUES)
            raise ValueError(f"unknown queue '{name}'. Allowed: {allowed}")
        if name not in selected:
            selected.append(name)

    return selected or list(ALL_QUEUES)


def redis_connection() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url)


def queue_depths(connection: Redis | None = None) -> dict[str, int]:
    own_connection = connection is None
    conn = connection or redis_connection()
    try:
        return {queue_name: Queue(queue_name, connection=conn).count for queue_name in ALL_QUEUES}
    finally:
        if own_connection:
            conn.close()


def refresh_queue_depth_metrics(connection: Redis | None = None) -> dict[str, int]:
    depths = queue_depths(connection)
    for queue_name, depth in depths.items():
        INGEST_BACKLOG_DEPTH.labels(queue=queue_name).set(depth)
    return depths


def _enqueue_job(
    queue_name: str,
    fn,
    *args,
    connection: Redis,
):
    settings = get_settings()
    queue = Queue(queue_name, connection=connection)
    return queue.enqueue(
        fn,
        *args,
        job_timeout=settings.worker_job_timeout_seconds,
        result_ttl=settings.worker_result_ttl_seconds,
        failure_ttl=settings.worker_failure_ttl_seconds,
    )


def enqueue_connector_sync(tool: str, *, connection: Redis | None = None) -> dict[str, str]:
    own_connection = connection is None
    conn = connection or redis_connection()
    try:
        ingest_job = _enqueue_job(
            CONNECTOR_INGEST_QUEUE, jobs.run_connector_ingest, tool, connection=conn
        )
        permissions_job = _enqueue_job(
            PERMISSIONS_SYNC_QUEUE,
            jobs.run_permissions_sync,
            tool,
            connection=conn,
        )
        refresh_queue_depth_metrics(conn)
        return {"ingest_job_id": ingest_job.id, "permissions_job_id": permissions_job.id}
    finally:
        if own_connection:
            conn.close()


def enqueue_cycle(
    *,
    include_identity: bool = True,
    include_aggregation: bool = True,
    connection: Redis | None = None,
) -> dict:
    own_connection = connection is None
    conn = connection or redis_connection()
    try:
        db = SessionLocal()
        try:
            tools = db.scalars(
                select(models.ConnectorConfig.tool)
                .where(models.ConnectorConfig.enabled.is_(True))
                .order_by(models.ConnectorConfig.tool.asc())
            ).all()
        finally:
            db.close()

        connector_jobs: dict[str, dict[str, str]] = {}
        for tool in tools:
            connector_jobs[tool] = enqueue_connector_sync(tool, connection=conn)

        identity_job_id = None
        if include_identity:
            identity_job_id = _enqueue_job(
                NORMALIZE_QUEUE, jobs.run_kg_and_identity, connection=conn
            ).id

        aggregation_job_id = None
        if include_aggregation:
            aggregation_job_id = _enqueue_job(
                AGGREGATE_CONTEXT_QUEUE, jobs.run_aggregation, connection=conn
            ).id

        depths = refresh_queue_depth_metrics(conn)
        return {
            "enabled_connectors": tools,
            "connector_jobs": connector_jobs,
            "identity_job_id": identity_job_id,
            "aggregation_job_id": aggregation_job_id,
            "queue_depths": depths,
        }
    finally:
        if own_connection:
            conn.close()


def run_worker(*, queues: list[str] | None = None, burst: bool = False) -> None:
    conn = redis_connection()
    queue_names = parse_queue_names(queues)
    queue_instances = [Queue(name, connection=conn) for name in queue_names]
    worker = Worker(queue_instances, connection=conn)
    refresh_queue_depth_metrics(conn)
    try:
        worker.work(burst=burst)
    finally:
        conn.close()


def run_scheduler(
    *,
    interval_seconds: int,
    once: bool = False,
    include_identity: bool = True,
    include_aggregation: bool = True,
) -> None:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be > 0")

    while True:
        enqueue_cycle(
            include_identity=include_identity,
            include_aggregation=include_aggregation,
        )
        if once:
            return
        time.sleep(interval_seconds)
