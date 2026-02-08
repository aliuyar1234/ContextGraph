from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from ocg.api.deps import get_db
from ocg.core.observability import metrics_response
from ocg.core.settings import get_settings

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    settings = get_settings()
    redis_client = Redis.from_url(settings.redis_url)
    try:
        redis_client.ping()
    finally:
        redis_client.close()
    return {"ready": True}


@router.get("/metrics")
def metrics():
    return metrics_response()
