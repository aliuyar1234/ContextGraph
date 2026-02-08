from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ocg.api.deps import get_db, require_admin
from ocg.connectors.registry import CONNECTOR_REGISTRY
from ocg.db import models
from ocg.services import ingest

router = APIRouter(prefix="/api/v1/admin/connectors", tags=["admin"])


class ConnectorEnableRequest(BaseModel):
    base_url: str | None = None
    auth: dict = Field(default_factory=dict)
    scopes: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    poll_interval_seconds: int = 120


class RetentionConfigRequest(BaseModel):
    retention_enabled: bool
    raw_days: int = Field(default=30, ge=1)
    trace_days: int = Field(default=180, ge=1)
    context_days: int = Field(default=365, ge=1)


@router.get("")
def list_connectors(
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(
        select(models.ConnectorConfig).order_by(models.ConnectorConfig.tool.asc())
    ).all()
    return {
        "connectors": [
            {
                "tool": row.tool,
                "enabled": row.enabled,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/{tool}/enable")
def enable_connector(
    tool: str,
    body: ConnectorEnableRequest,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    connector = CONNECTOR_REGISTRY.get(tool)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not supported.")
    config = body.model_dump()
    connector.validate(config)
    row = ingest.set_connector_enabled(db, tool, True, config)
    return {"tool": tool, "enabled": row.enabled}


@router.post("/{tool}/disable")
def disable_connector(
    tool: str, _admin=Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    connector = CONNECTOR_REGISTRY.get(tool)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not supported.")
    row = ingest.set_connector_enabled(db, tool, False, {"disabled": True})
    return {"tool": tool, "enabled": row.enabled}


@router.post("/{tool}/sync_now")
def sync_now(tool: str, _admin=Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    connector = CONNECTOR_REGISTRY.get(tool)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not supported.")
    config = db.scalar(select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool))
    if not config or not config.enabled:
        raise HTTPException(status_code=409, detail="Connector is disabled.")
    ingest_result = ingest.ingest_connector_batch(db, connector, config.config_json)
    sync_result = ingest.sync_permissions(db, connector, config.config_json)
    return {"ingest": ingest_result, "permissions_sync": sync_result}


@router.get("/{tool}/health")
def connector_health(
    tool: str, _admin=Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    config = db.scalar(select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool))
    if not config:
        raise HTTPException(status_code=404, detail="Connector not configured.")
    return {
        "tool": tool,
        "enabled": config.enabled,
        "last_checked_at": datetime.now(tz=UTC).isoformat(),
        "status": "healthy" if config.enabled else "disabled",
    }


@router.get("/retention")
def get_retention(_admin=Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    row = db.get(models.JobCheckpoint, "retention_config")
    config = (
        row.checkpoint_json
        if row
        else {"retention_enabled": True, "raw_days": 30, "trace_days": 180, "context_days": 365}
    )
    return {"retention": config}


@router.post("/retention")
def set_retention(
    body: RetentionConfigRequest,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(models.JobCheckpoint, "retention_config")
    payload = body.model_dump()
    if row is None:
        row = models.JobCheckpoint(
            job_name="retention_config",
            checkpoint_json=payload,
            updated_at=datetime.now(tz=UTC),
        )
        db.add(row)
    else:
        row.checkpoint_json = payload
        row.updated_at = datetime.now(tz=UTC)
    db.add(
        models.AuditLog(
            actor_principal_id="admin",
            action="retention_update",
            metadata_json=payload,
            created_at=datetime.now(tz=UTC),
        )
    )
    db.commit()
    return {"retention": payload}
