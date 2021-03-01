# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Shared plugin state, maintained as singleton objects.
"""

import operator
from collections import deque
from logging import Logger
from typing import Deque, Dict, List, Optional

from .config import Config
from .meeting import Meeting

_COMPLETED_SIZE = 16  # size of the _COMPLETED deque

_LOGGER: Logger
_CONFIG: Config
_ACTIVE: Dict[str, Meeting] = {}
_COMPLETED: Deque[Meeting] = deque([], _COMPLETED_SIZE)

# noinspection PyShadowingNames
def set_logger(logger: Logger) -> None:  # pylint: disable=redefined-outer-name:
    """Set the shared logger instance."""
    global _LOGGER  # pylint: disable=global-statement:
    _LOGGER = logger


def logger() -> Logger:
    """Give the rest of the plugin access to a shared logger instance."""
    return _LOGGER


# noinspection PyShadowingNames
def set_config(config: Config) -> None:  # pylint: disable=redefined-outer-name:
    """Set shared configuration."""
    global _CONFIG  # pylint: disable=global-statement:
    _CONFIG = config


def config() -> Config:
    """Give the rest of the plugin access to shared configuration."""
    return _CONFIG


def get_meeting(channel: str, network: str) -> Optional[Meeting]:
    try:
        key = Meeting.meeting_key(channel, network)
        return _ACTIVE[key]
    except KeyError:
        return None


def get_meetings(active: bool, completed: bool) -> List[Meeting]:
    """Return a list of tracked meetings, optionally filtering out active or completed meetings."""
    meetings: List[Meeting] = []
    if active:
        meetings += _ACTIVE.values()
    if completed:
        meetings += _COMPLETED
    meetings.sort(key=operator.itemgetter("end_date", "start_date"))
    return meetings


def move_to_complete(meeting: Meeting) -> None:
    """Move a meeting from active to completed."""
    key = meeting.key()
    popped = _ACTIVE.pop(key)
    assert popped is meeting  # if they're not the same, something is broken
    _COMPLETED.append(popped)  # will potentially roll off an older meeting
