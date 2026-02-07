import pytest

from ocg.services.reliability import RetryPolicy, retry_with_backoff


class RetryableError(RuntimeError):
    pass


def test_retries_are_bounded():
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        raise RetryableError("rate limited")

    with pytest.raises(RetryableError):
        retry_with_backoff(
            fn,
            policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.0, max_delay_seconds=0.0),
            retryable=lambda exc: isinstance(exc, RetryableError),
        )
    assert attempts["count"] == 3

