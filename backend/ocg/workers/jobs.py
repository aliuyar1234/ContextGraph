from sqlalchemy import select

from ocg.connectors.registry import CONNECTOR_REGISTRY
from ocg.core.settings import get_settings
from ocg.db import models
from ocg.db.session import SessionLocal
from ocg.services import aggregation, identity, ingest, kg, personal


def run_connector_ingest(tool: str) -> dict:
    settings = get_settings()
    db = SessionLocal()
    try:
        config_row = db.scalar(
            select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool)
        )
        if not config_row or not config_row.enabled:
            return {"status": "skipped", "reason": "connector disabled"}
        connector = CONNECTOR_REGISTRY[tool]
        result = ingest.ingest_connector_batch(db, connector, config_row.config_json)
        return {"status": "ok", "result": result}
    finally:
        db.close()


def run_permissions_sync(tool: str) -> dict:
    db = SessionLocal()
    try:
        config_row = db.scalar(
            select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool)
        )
        if not config_row or not config_row.enabled:
            return {"status": "skipped", "reason": "connector disabled"}
        connector = CONNECTOR_REGISTRY[tool]
        result = ingest.sync_permissions(db, connector, config_row.config_json)
        return {"status": "ok", "result": result}
    finally:
        db.close()


def run_personal_graph(person_id: str, principal_ids: list[str]) -> dict:
    db = SessionLocal()
    try:
        timeline_count = personal.build_personal_timeline(db, person_id, principal_ids)
        task_count = personal.cluster_personal_tasks(db, person_id)
        return {"status": "ok", "timeline_items": timeline_count, "tasks": task_count}
    finally:
        db.close()


def run_kg_and_identity() -> dict:
    db = SessionLocal()
    try:
        identities = identity.resolve_identities(db)
        entities = kg.infer_kg_entities(db)
        return {"status": "ok", "identities": identities, "kg": entities}
    finally:
        db.close()


def run_aggregation() -> dict:
    settings = get_settings()
    db = SessionLocal()
    try:
        if not settings.retention_enabled:
            return {"status": "skipped", "reason": "retention disabled blocks publication"}
        abstracted = aggregation.abstract_opted_in_traces(db)
        published = aggregation.cluster_and_publish(db, settings)
        return {"status": "ok", "abstracted": abstracted, "published": published}
    finally:
        db.close()

