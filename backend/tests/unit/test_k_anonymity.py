from datetime import timedelta

from ocg.core.settings import Settings
from ocg.db import models
from ocg.services import aggregation


def test_k_anonymity_prevents_publish_below_threshold(db_session, now):
    traces = [
        models.AbstractTrace(
            process_key="tickets:action=status_change",
            steps_json=[
                {
                    "action_type": "status_change",
                    "tool_family": "tickets",
                    "entity_type_tags": ["Ticket"],
                    "process_tags": ["action:status_change"],
                    "delta_time_ms_from_prev": 0,
                }
            ],
            outcome="resolved_fast",
            created_at=now + timedelta(minutes=i),
            eligible=True,
            source_person_id_hash=f"user-{i}",
        )
        for i in range(2)
    ]
    db_session.add_all(traces)
    db_session.commit()

    settings = Settings(k_anonymity_k=5, k_anonymity_n=20)
    result = aggregation.cluster_and_publish(db_session, settings)
    assert result["published"] == 0
    assert result["dropped"] >= 1
    patterns = db_session.query(models.ContextPattern).all()
    assert all(pattern.published is False for pattern in patterns)
