import pytest

from ocg.workers import runtime
from ocg.workers.queues import ALL_QUEUES


def test_parse_queue_names_defaults_to_all():
    assert runtime.parse_queue_names(None) == list(ALL_QUEUES)


def test_parse_queue_names_deduplicates_and_keeps_order():
    parsed = runtime.parse_queue_names("connector_ingest,permissions_sync,connector_ingest")
    assert parsed == ["connector_ingest", "permissions_sync"]


def test_parse_queue_names_rejects_unknown():
    with pytest.raises(ValueError):
        runtime.parse_queue_names("unknown_queue")


def test_scheduler_rejects_non_positive_interval():
    with pytest.raises(ValueError):
        runtime.run_scheduler(interval_seconds=0, once=True)
