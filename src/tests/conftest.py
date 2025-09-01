import os
import time


def pytest_sessionstart(session):  # noqa: ARG001
    """Explicitly set the UTC timezone for all tests."""
    os.environ["TZ"] = "UTC"
    time.tzset()
