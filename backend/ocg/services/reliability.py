from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.1
    max_delay_seconds: float = 1.0


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    policy: RetryPolicy,
    retryable: Callable[[Exception], bool],
) -> T:
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if attempt >= policy.max_attempts or not retryable(exc):
                raise
            sleep_for = min(
                policy.base_delay_seconds * (2 ** (attempt - 1)), policy.max_delay_seconds
            )
            sleep_for = sleep_for + random.uniform(0, sleep_for / 2)
            time.sleep(sleep_for)
