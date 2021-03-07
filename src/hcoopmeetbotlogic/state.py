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


# Following the pattern from the original MeetBot, global variables
# that need to be initialized are defined in a try/except block.  This is
# done to avoid wiping out state across plugin reloads.  If the variable
# is already defined, it will be unchanged.  If it's not defined, it will
# be initialized. This looks a little odd, but does seem to work.

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    _LOGGER  # type: ignore
except NameError:
    _LOGGER = None

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    _CONFIG  # type: ignore
except NameError:
    _CONFIG = None

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    _ACTIVE
except NameError:
    _ACTIVE: Dict[str, Meeting] = {}

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    _COMPLETED
except NameError:
    _COMPLETED: Deque[Meeting] = deque([], _COMPLETED_SIZE)


# noinspection PyShadowingNames
def set_logger(logger: Logger) -> None:  # pylint: disable=redefined-outer-name:
    """Set the shared logger instance."""
    global _LOGGER  # pylint: disable=global-statement:
    _LOGGER = logger


# noinspection PyTypeChecker
def logger() -> Logger:
    """Give the rest of the plugin access to a shared logger instance."""
    if _LOGGER is None:
        raise RuntimeError("Plugin state not initialized; call set_logger() before logger()")
    return _LOGGER


# noinspection PyShadowingNames
def set_config(config: Config) -> None:  # pylint: disable=redefined-outer-name:
    """Set shared configuration."""
    global _CONFIG  # pylint: disable=global-statement:
    _CONFIG = config


# noinspection PyTypeChecker
def config() -> Config:
    """Give the rest of the plugin access to shared configuration."""
    if _CONFIG is None:
        raise RuntimeError("Plugin state not initialized; call set_config() before config()")
    return _CONFIG


def add_meeting(nick: str, channel: str, network: str) -> Meeting:
    """Add a new active meeting."""
    meeting = Meeting(founder=nick, channel=channel, network=network)
    _ACTIVE[meeting.key()] = meeting
    return meeting


def deactivate_meeting(meeting: Meeting, retain: bool = True) -> None:
    """Move a meeting out of the active list, optionally retaining it in the completed list."""
    key = meeting.key()
    assert key in _ACTIVE  # if the key is not tracked, something is screwed up
    popped = _ACTIVE.pop(key)
    assert popped is meeting  # if they're not the same, something is screwed up
    if retain:
        _COMPLETED.append(popped)  # will potentially roll off an older meeting


def get_meeting(channel: str, network: str) -> Optional[Meeting]:
    """Get a meeting for the channel and network."""
    try:
        key = Meeting.meeting_key(channel, network)
        return _ACTIVE[key]
    except KeyError:
        return None


def get_meetings(active: bool = True, completed: bool = True) -> List[Meeting]:
    """Return a list of tracked meetings, optionally filtering out active or completed meetings."""
    meetings: List[Meeting] = []
    if active:
        meetings += _ACTIVE.values()
    if completed:
        meetings += _COMPLETED
    meetings.sort(key=operator.attrgetter("end_time", "start_time"))
    return meetings
