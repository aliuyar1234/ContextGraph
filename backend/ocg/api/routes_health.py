from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ocg.api.deps import get_db
from ocg.core.observability import metrics_response

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"ready": True}


@router.get("/metrics")
def metrics():
    return metrics_response()

