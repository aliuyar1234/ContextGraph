from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ocg.api.deps import get_db, require_analytics_role
from ocg.services import analytics

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/processes")
def processes(_viewer=Depends(require_analytics_role), db: Session = Depends(get_db)) -> dict:
    return {"processes": analytics.list_processes(db)}


@router.get("/processes/{process_key}/patterns")
def process_patterns(
    process_key: str, _viewer=Depends(require_analytics_role), db: Session = Depends(get_db)
) -> dict:
    return {"patterns": analytics.list_patterns(db, process_key)}


@router.get("/processes/{process_key}/variants")
def process_variants(
    process_key: str, _viewer=Depends(require_analytics_role), db: Session = Depends(get_db)
) -> dict:
    patterns = analytics.list_patterns(db, process_key)
    if not patterns:
        raise HTTPException(status_code=404, detail="Process not found.")
    pattern_id = patterns[0]["pattern_id"]
    variants = analytics.pattern_variants(db, pattern_id)
    return {"process_key": process_key, "pattern_id": pattern_id, "variants": variants}


@router.get("/patterns/{pattern_id}/variants")
def pattern_variants(
    pattern_id: str, _viewer=Depends(require_analytics_role), db: Session = Depends(get_db)
) -> dict:
    variants = analytics.pattern_variants(db, pattern_id)
    if not variants:
        raise HTTPException(status_code=404, detail="Pattern not found.")
    return {"pattern_id": pattern_id, "k_anonymous": True, "variants": variants}


@router.get("/patterns/{pattern_id}/edges")
def pattern_edges(
    pattern_id: str, _viewer=Depends(require_analytics_role), db: Session = Depends(get_db)
) -> dict:
    return {"pattern_id": pattern_id, "edges": analytics.pattern_edges(db, pattern_id)}


@router.get("/patterns/{pattern_id}/bottlenecks")
def pattern_bottlenecks(
    pattern_id: str, _viewer=Depends(require_analytics_role), db: Session = Depends(get_db)
) -> dict:
    return {"pattern_id": pattern_id, "bottlenecks": analytics.bottlenecks(db, pattern_id)}
