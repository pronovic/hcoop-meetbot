# vim: set ft=python ts=4 sw=4 expandtab:

"""
Date utilities.
"""

from datetime import datetime

from pytz import timezone, utc


def now() -> datetime:
    """Get the current time in UTC"""
    return datetime.now(utc)


def formatdate(timestamp: datetime | None, zone: str = "UTC", fmt: str = "%Y-%m-%dT%H:%M%z") -> str:
    """Format a datetime for display in a specific time zone."""
    return timestamp.astimezone(timezone(zone)).strftime(fmt) if timestamp else "None"
