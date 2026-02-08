from collections.abc import Sequence

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ocg.core.observability import PERMISSION_UNKNOWN
from ocg.db import models


class PermissionEvaluator:
    """Single permission evaluator used by API and workers."""

    @staticmethod
    def resource_visible_to_principals(
        db: Session, *, resource_id: str, principal_ids: Sequence[str]
    ) -> bool:
        resource = db.get(models.Resource, resource_id)
        if resource is None:
            return False
        if resource.permission_state != "KNOWN":
            PERMISSION_UNKNOWN.inc()
            return False

        acl_rows = db.scalars(
            select(models.ResourceACL).where(
                and_(
                    models.ResourceACL.resource_id == resource_id,
                    models.ResourceACL.revoked_at.is_(None),
                )
            )
        ).all()
        if not acl_rows:
            # Public-within-org semantics are tool-specific; default fail-closed.
            return False
        allowed = {row.principal_id for row in acl_rows}
        return bool(allowed.intersection(set(principal_ids)))

    @staticmethod
    def event_visible_to_principals(
        db: Session, *, event: models.TraceEvent, principal_ids: Sequence[str]
    ) -> bool:
        if event.permission_state != "KNOWN":
            PERMISSION_UNKNOWN.inc()
            return False
        if not event.resource_id:
            return True
        return PermissionEvaluator.resource_visible_to_principals(
            db, resource_id=event.resource_id, principal_ids=principal_ids
        )
