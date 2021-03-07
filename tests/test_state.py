# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock

import pytest

from hcoopmeetbotlogic.state import (
    _ACTIVE,
    _COMPLETED,
    _COMPLETED_SIZE,
    _CONFIG,
    _LOGGER,
    add_meeting,
    config,
    deactivate_meeting,
    get_meeting,
    get_meetings,
    logger,
    set_config,
    set_logger,
)


class TestFunctions:
    def test_logger_behavior(self):
        if _LOGGER is None:
            with pytest.raises(RuntimeError):
                logger()
        stub = MagicMock()
        set_logger(stub)
        assert logger() is stub

    def test_config_behavior(self):
        if _CONFIG is None:
            with pytest.raises(RuntimeError):
                config()
        stub = MagicMock()
        set_config(stub)
        assert config() is stub

    def test_add_meeting(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        meeting = add_meeting("nick", "channel", "network")
        assert meeting.founder == "nick"
        assert meeting.channel == "channel"
        assert meeting.network == "network"
        assert _ACTIVE[meeting.key()] is meeting

    def test_deactivate_meeting_not_retained(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        meeting = add_meeting("nick", "channel", "network")
        deactivate_meeting(meeting, retain=False)
        assert len(_ACTIVE) == 0
        assert len(_COMPLETED) == 0

    def test_deactivate_meeting_retained(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        meeting = add_meeting("nick", "channel", "network")
        deactivate_meeting(meeting, retain=True)
        assert len(_ACTIVE) == 0
        assert meeting in _COMPLETED

    def test_completed_size_limit(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        meetings = []

        # Until we hit the limit, every meeting that we deactivate should stay in _COMPLETED
        for _ in range(0, _COMPLETED_SIZE):
            meeting = add_meeting("nick", "channel", "network")
            deactivate_meeting(meeting, retain=True)
            meetings.append(meeting)
            assert len(_COMPLETED) == len(meetings)
            for meeting in meetings:
                assert meeting in _COMPLETED

        # the next one we deactivate should roll one item off _COMPLETED
        meeting = add_meeting("nick", "channel", "network")
        deactivate_meeting(meeting, retain=True)
        meetings.append(meeting)
        assert len(_COMPLETED) == len(meetings) - 1
        assert meetings[0] not in _COMPLETED
        for meeting in meetings[1:]:
            assert meeting in _COMPLETED

        # and so forth...
        meeting = add_meeting("nick", "channel", "network")
        deactivate_meeting(meeting, retain=True)
        meetings.append(meeting)
        assert len(_COMPLETED) == len(meetings) - 2
        assert meetings[0] not in _COMPLETED
        assert meetings[1] not in _COMPLETED
        for meeting in meetings[2:]:
            assert meeting in _COMPLETED

    def test_get_meeting(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        assert get_meeting("channel", "network") is None
        meeting = add_meeting("nick", "channel", "network")
        assert get_meeting("channel", "network") is meeting

    def test_get_meetings(self):
        _ACTIVE.clear()
        _COMPLETED.clear()
        active1 = add_meeting("a1-nick", "a1-channel", "a1-network")
        active2 = add_meeting("a2-nick", "a2-channel", "a2-network")
        completed1 = add_meeting("c1-nick", "c1-channel", "c1-network")
        completed2 = add_meeting("c2-nick", "c2-channel", "c12-network")
        deactivate_meeting(completed1, retain=True)
        deactivate_meeting(completed2, retain=True)
        assert get_meetings(active=False, completed=False) == []
        assert get_meetings(active=True, completed=False) == [active1, active2]
        assert get_meetings(active=False, completed=True) == [completed1, completed2]
        assert get_meetings(active=True, completed=True) == [active1, active2, completed1, completed2]
