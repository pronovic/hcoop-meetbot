# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Common utilities.
"""
from datetime import datetime
from typing import Optional

from pytz import timezone, utc


def now() -> datetime:
    """Get the current time in UTC"""
    return datetime.now(utc)


def formatdate(timestamp: Optional[datetime], zone: str = "UTC", fmt: str = "%Y-%m-%dT%H:%M%z") -> str:
    """Format a datetime for display in a specific time zone."""
    return timestamp.astimezone(timezone(zone)).strftime(fmt) if timestamp else "None"
