from ocg.connectors.registry import CONNECTOR_REGISTRY
from ocg.core.settings import Settings
from ocg.db import models
from ocg.services import aggregation, identity, ingest, kg, personal
from ocg.services.common import utcnow


def _seed_person(db, person_id: str) -> None:
    if db.get(models.Person, person_id):
        person_exists = True
    else:
        person_exists = False
    if not person_exists:
        db.add(models.Person(person_id=person_id, primary_email=None, display_name=person_id, created_at=utcnow()))
    if not db.get(models.Principal, person_id):
        db.add(
            models.Principal(
                principal_id=person_id,
                principal_type="user",
                person_id=person_id,
                external_group_ref=None,
                created_at=utcnow(),
            )
        )
    db.commit()


def test_ingest_to_analytics_pipeline(db_session):
    for tool, connector in CONNECTOR_REGISTRY.items():
        config = {"auth": {"token_ref": f"env:{tool.upper()}_TOKEN"}, "scopes": ["read:default"]}
        ingest.set_connector_enabled(db_session, tool, True, config)
        ingest.ingest_connector_batch(db_session, connector, config)
        ingest.sync_permissions(db_session, connector, config)

    identity.resolve_identities(db_session)
    kg.infer_kg_entities(db_session)
    _seed_person(db_session, "demo-user")
    personal.set_opt_in(db_session, "demo-user", True)
    personal.build_personal_timeline(
        db_session, "demo-user", ["demo-user", "group:analyst", "group:admin"]
    )
    personal.cluster_personal_tasks(db_session, "demo-user")

    aggregation.abstract_opted_in_traces(db_session)
    settings = Settings(k_anonymity_k=1, k_anonymity_n=1)
    published = aggregation.cluster_and_publish(db_session, settings)
    assert published["published"] >= 1

    suggestions = aggregation.suggest_next_steps(
        db_session, process_key="chat:action=message", recent_steps=[], limit=5
    )
    assert isinstance(suggestions, list)
