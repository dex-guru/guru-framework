from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class ExternalTaskConfig:
    max_tasks: int = 1

    retries: int = 3

    lock_duration: timedelta = timedelta(seconds=60)

    async_response_timeout: timedelta = timedelta(seconds=30)

    retry_timeout: timedelta = timedelta(seconds=30)

    sleep_seconds: timedelta = timedelta(seconds=30)

    auto_extend_lock: bool = False
