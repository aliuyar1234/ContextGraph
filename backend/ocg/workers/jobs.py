from sqlalchemy import select

from ocg.connectors.registry import CONNECTOR_REGISTRY
from ocg.core.observability import WORKER_JOB_DURATION, WORKER_JOBS_TOTAL, traced_span
from ocg.core.settings import get_settings
from ocg.db import models
from ocg.db.session import SessionLocal
from ocg.services import aggregation, identity, ingest, kg, personal


def run_connector_ingest(tool: str) -> dict[str, object]:
    db = SessionLocal()
    status = "error"
    try:
        with traced_span("worker.connector_ingest"):
            with WORKER_JOB_DURATION.labels(job="connector_ingest").time():
                config_row = db.scalar(
                    select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool)
                )
                if not config_row or not config_row.enabled:
                    payload: dict[str, object] = {
                        "status": "skipped",
                        "reason": "connector disabled",
                    }
                    status = str(payload["status"])
                    return payload
                connector = CONNECTOR_REGISTRY[tool]
                result = ingest.ingest_connector_batch(db, connector, config_row.config_json)
                payload = {"status": "ok", "result": result}
                status = str(payload["status"])
                return payload
    except Exception:
        status = "error"
        raise
    finally:
        WORKER_JOBS_TOTAL.labels(job="connector_ingest", status=status).inc()
        db.close()


def run_permissions_sync(tool: str) -> dict[str, object]:
    db = SessionLocal()
    status = "error"
    try:
        with traced_span("worker.permissions_sync"):
            with WORKER_JOB_DURATION.labels(job="permissions_sync").time():
                config_row = db.scalar(
                    select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool)
                )
                if not config_row or not config_row.enabled:
                    payload: dict[str, object] = {
                        "status": "skipped",
                        "reason": "connector disabled",
                    }
                    status = str(payload["status"])
                    return payload
                connector = CONNECTOR_REGISTRY[tool]
                result = ingest.sync_permissions(db, connector, config_row.config_json)
                payload = {"status": "ok", "result": result}
                status = str(payload["status"])
                return payload
    except Exception:
        status = "error"
        raise
    finally:
        WORKER_JOBS_TOTAL.labels(job="permissions_sync", status=status).inc()
        db.close()


def run_personal_graph(person_id: str, principal_ids: list[str]) -> dict[str, object]:
    db = SessionLocal()
    status = "error"
    try:
        with traced_span("worker.personal_graph"):
            with WORKER_JOB_DURATION.labels(job="personal_graph").time():
                timeline_count = personal.build_personal_timeline(db, person_id, principal_ids)
                task_count = personal.cluster_personal_tasks(db, person_id)
                payload: dict[str, object] = {
                    "status": "ok",
                    "timeline_items": timeline_count,
                    "tasks": task_count,
                }
                status = str(payload["status"])
                return payload
    except Exception:
        status = "error"
        raise
    finally:
        WORKER_JOBS_TOTAL.labels(job="personal_graph", status=status).inc()
        db.close()


def run_kg_and_identity() -> dict[str, object]:
    db = SessionLocal()
    status = "error"
    try:
        with traced_span("worker.kg_identity"):
            with WORKER_JOB_DURATION.labels(job="kg_identity").time():
                identities = identity.resolve_identities(db)
                entities = kg.infer_kg_entities(db)
                payload: dict[str, object] = {
                    "status": "ok",
                    "identities": identities,
                    "kg": entities,
                }
                status = str(payload["status"])
                return payload
    except Exception:
        status = "error"
        raise
    finally:
        WORKER_JOBS_TOTAL.labels(job="kg_identity", status=status).inc()
        db.close()


def run_aggregation() -> dict[str, object]:
    settings = get_settings()
    db = SessionLocal()
    status = "error"
    try:
        with traced_span("worker.aggregation"):
            with WORKER_JOB_DURATION.labels(job="aggregation").time():
                if not settings.retention_enabled:
                    payload: dict[str, object] = {
                        "status": "skipped",
                        "reason": "retention disabled blocks publication",
                    }
                    status = str(payload["status"])
                    return payload
                abstracted = aggregation.abstract_opted_in_traces(db)
                published = aggregation.cluster_and_publish(db, settings)
                payload = {
                    "status": "ok",
                    "abstracted": abstracted,
                    "published": published,
                }
                status = str(payload["status"])
                return payload
    except Exception:
        status = "error"
        raise
    finally:
        WORKER_JOBS_TOTAL.labels(job="aggregation", status=status).inc()
        db.close()
