from sqlalchemy import select
from sqlalchemy.orm import Session

from ocg.db import models


def infer_kg_entities(db: Session) -> dict[str, int]:
    events = db.scalars(select(models.TraceEvent)).all()
    created_entities = 0
    created_edges = 0
    for event in events:
        tags = event.entity_tags_json or {}
        for entity_type in tags.get("entity_type_tags", []):
            key = f"{entity_type.lower()}:{event.tool}"
            pending_entity_exists = any(
                isinstance(pending, models.KGEntity) and pending.entity_id == key
                for pending in db.new
            )
            entity = db.scalar(select(models.KGEntity).where(models.KGEntity.canonical_key == key))
            if not entity and not pending_entity_exists:
                entity = models.KGEntity(
                    entity_id=key,
                    entity_type=entity_type,
                    canonical_key=key,
                    display_name=key,
                    confidence=0.6,
                    attrs_json={"tool": event.tool},
                )
                db.add(entity)
                created_entities += 1

            person_entity_id = f"person:{event.actor_principal_id or 'unknown'}"
            pending_person_exists = any(
                isinstance(pending, models.KGEntity) and pending.entity_id == person_entity_id
                for pending in db.new
            )
            person_entity = db.scalar(
                select(models.KGEntity).where(models.KGEntity.entity_id == person_entity_id)
            )
            if not person_entity and not pending_person_exists:
                db.add(
                    models.KGEntity(
                        entity_id=person_entity_id,
                        entity_type="Person",
                        canonical_key=person_entity_id,
                        display_name=person_entity_id,
                        confidence=0.7,
                        attrs_json={},
                    )
                )
            edge_exists = db.scalar(
                select(models.KGEdge).where(
                    models.KGEdge.src_entity_id == person_entity_id,
                    models.KGEdge.dst_entity_id == key,
                    models.KGEdge.edge_type == "acts_on",
                )
            )
            if not edge_exists:
                db.add(
                    models.KGEdge(
                        src_entity_id=person_entity_id,
                        dst_entity_id=key,
                        edge_type="acts_on",
                        confidence=0.5,
                        evidence_trace_event_ids=[event.trace_event_id],
                    )
                )
                created_edges += 1
    db.commit()
    return {"entities_created": created_entities, "edges_created": created_edges}
