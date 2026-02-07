from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ocg.api.deps import get_auth_context, get_db
from ocg.core.security import AuthContext
from ocg.services import personal

router = APIRouter(prefix="/api/v1/personal", tags=["personal"])


@router.get("/timeline")
def timeline(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    personal.build_personal_timeline(db, context.person_id, context.principal_ids)
    return {"items": personal.personal_timeline(db, context.person_id, from_, to)}


@router.get("/tasks")
def tasks(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    _ = from_, to
    personal.build_personal_timeline(db, context.person_id, context.principal_ids)
    personal.cluster_personal_tasks(db, context.person_id)
    return {"tasks": personal.personal_tasks(db, context.person_id)}


class OptInRequest(BaseModel):
    enabled: bool


@router.post("/opt_in_aggregation")
def opt_in_aggregation(
    body: OptInRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    row = personal.set_opt_in(db, context.person_id, body.enabled)
    return {"person_id": row.person_id, "opt_in_aggregation": row.opt_in_aggregation}

