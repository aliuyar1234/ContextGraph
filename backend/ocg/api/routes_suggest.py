from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ocg.api.deps import get_db, require_analytics_role
from ocg.services import aggregation

router = APIRouter(prefix="/api/v1/suggest", tags=["suggest"])


class StepIn(BaseModel):
    action_type: str
    tool_family: str
    process_tags: list[str] = Field(default_factory=list)
    entity_type_tags: list[str] = Field(default_factory=list)


class NextStepsRequest(BaseModel):
    process_key: str
    recent_steps: list[StepIn] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/next_steps")
def next_steps(
    body: NextStepsRequest,
    _viewer=Depends(require_analytics_role),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "next_steps": aggregation.suggest_next_steps(
            db,
            process_key=body.process_key,
            recent_steps=[item.model_dump() for item in body.recent_steps],
            limit=body.limit,
        )
    }

