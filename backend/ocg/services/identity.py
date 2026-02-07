from collections import defaultdict
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from ocg.db import models
from ocg.services.common import utcnow


def ensure_person_and_principal(db: Session, person_id: str, email: str | None = None) -> None:
    pending_person = any(
        isinstance(pending, models.Person) and pending.person_id == person_id for pending in db.new
    )
    person = db.get(models.Person, person_id)
    if not person and not pending_person:
        db.add(
            models.Person(
                person_id=person_id,
                primary_email=email,
                display_name=person_id,
                created_at=utcnow(),
            )
        )
    pending_principal = any(
        isinstance(pending, models.Principal) and pending.principal_id == person_id
        for pending in db.new
    )
    principal = db.get(models.Principal, person_id)
    if not principal and not pending_principal:
        db.add(
            models.Principal(
                principal_id=person_id,
                principal_type="user",
                person_id=person_id,
                external_group_ref=None,
                created_at=utcnow(),
            )
        )


def resolve_identities(db: Session) -> dict[str, int]:
    rows = db.scalars(select(models.TraceEvent)).all()
    created = 0
    for event in rows:
        actor = event.actor_principal_id
        if not actor:
            continue
        email = f"{actor}@ocg.local"
        ensure_person_and_principal(db, actor, email=email)
        identity = db.scalar(
            select(models.Identity).where(
                models.Identity.tool == event.tool, models.Identity.external_user_id == actor
            )
        )
        if not identity:
            db.add(
                models.Identity(
                    tool=event.tool,
                    external_user_id=actor,
                    email=email,
                    display_name=actor,
                    person_id=actor,
                    confidence=0.7,
                    created_at=utcnow(),
                )
            )
            created += 1

    # Baseline group membership from role groups.
    groups: dict[str, set[str]] = defaultdict(set)
    principals = db.scalars(select(models.Principal)).all()
    for principal in principals:
        if principal.principal_type == "user":
            groups["group:user"].add(principal.principal_id)
    for group, members in groups.items():
        if not db.get(models.Principal, group):
            db.add(
                models.Principal(
                    principal_id=group,
                    principal_type="group",
                    person_id=None,
                    external_group_ref=group,
                    created_at=utcnow(),
                )
            )
        for member in members:
            exists = db.get(
                models.PrincipalMembership,
                {"group_principal_id": group, "member_principal_id": member},
            )
            if not exists:
                db.add(
                    models.PrincipalMembership(
                        group_principal_id=group,
                        member_principal_id=member,
                        created_at=utcnow(),
                    )
                )
    db.commit()
    return {"identities_created": created}


def hash_person(person_id: str) -> str:
    return sha256(person_id.encode("utf-8")).hexdigest()
