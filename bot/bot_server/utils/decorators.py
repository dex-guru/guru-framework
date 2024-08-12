import time

from pathlib import Path

from bot_server.core.config import settings


class HealthCheck:
    """
    Health check decorator class. It touches the "healthy" file.
    If the worker is not alive, K8s kills the process.

    IMPORTANT:
    This decorator should be set on the periodically called function.
    It needs to set livenessProbe in the helm chart.

    Usage:

    def main():
        while True:
            foo()

    @HealthCheck
    def foo():
        do_something()

    if __name__ == '__main__':
        main()
    """

    def __init__(self, func):
        self.timeout = settings.HEALTH_CHECK_TIMEOUT
        self._last_check = time.monotonic()
        self.func = func
        Path("/tmp/healthy").touch()

    def im_alive(self):
        if time.monotonic() - self._last_check > self.timeout / 3:
            Path("/tmp/healthy").touch()
            self._last_check = time.monotonic()

    def __call__(self, *args, **kwargs):
        self.im_alive()
        return self.func(*args, **kwargs)
