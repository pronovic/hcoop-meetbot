# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from datetime import datetime
from unittest.mock import MagicMock, patch

from pytz import utc

from hcoopmeetbotlogic.interface import Message
from hcoopmeetbotlogic.meeting import EventType, Meeting, TrackedEvent, TrackedMessage


class TestTrackedMessage:
    def test_constructor(self):
        before = datetime.now(utc)
        message = TrackedMessage("sender", "payload", False)
        assert message.id is not None
        assert message.sender == "sender"
        assert message.payload == "payload"
        assert message.action is False
        assert message.timestamp >= before

    @patch("hcoopmeetbotlogic.meeting.formatdate")
    def test_display_name(self, formatdate):
        formatdate.return_value = "11111"
        timestamp = MagicMock()
        message = TrackedMessage("sender", "payload", False, id="whatever", timestamp=timestamp)
        assert message.display_name() == "whatever@11111"
        formatdate.assert_called_once_with(timestamp)


class TestTrackedEvent:
    def test_constructor(self):
        timestamp = MagicMock()
        message = MagicMock(timestamp=timestamp)
        attributes = {"a": "A"}
        event = TrackedEvent(EventType.LURK, message, attributes)
        assert event.id is not None
        assert event.event_type == EventType.LURK
        assert event.message is message
        assert event.attributes is attributes
        assert event.timestamp is timestamp

    @patch("hcoopmeetbotlogic.meeting.formatdate")
    def test_display_name(self, formatdate):
        formatdate.return_value = "11111"
        timestamp = MagicMock()
        message = MagicMock(timestamp=timestamp)
        attributes = {"a": "A"}
        event = TrackedEvent(EventType.LURK, message, attributes, id="whatever")
        assert event.display_name() == "whatever@11111"
        formatdate.assert_called_once_with(timestamp)


class TestMeeting:
    def test_constructor(self):
        before = datetime.now(utc)
        meeting = Meeting("nick", "channel", "network")
        assert meeting.id is not None
        assert meeting.name == "channel"
        assert meeting.founder == "nick"
        assert meeting.channel == "channel"
        assert meeting.network == "network"
        assert meeting.lurk is False
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick"]
        assert meeting.nicks == {"nick": 0}
        assert meeting.start_time >= before
        assert meeting.end_time is None
        assert meeting.original_topic is None
        assert meeting.meeting_topic is None
        assert meeting.current_topic is None
        assert meeting.messages == []
        assert meeting.events == []
        assert meeting.key() == "channel/network"
        assert meeting.active() is True

    def test_meeting_key(self):
        assert Meeting.meeting_key("channel", "network") == "channel/network"

    @patch("hcoopmeetbotlogic.meeting.formatdate")
    def test_display_name(self, formatdate):
        formatdate.return_value = "11111"
        meeting = Meeting("n", "c", "n")
        meeting.start_time = datetime(2021, 3, 7, 13, 14, 0)  # in UTC by default
        assert meeting.display_name() == "c/n@11111"
        formatdate.assert_called_once_with(meeting.start_time)

    def test_mark_completed(self):
        meeting = Meeting("nick", "channel", "network")
        meeting.mark_completed()
        assert meeting.active() is False
        assert meeting.end_time >= meeting.start_time

    # pylint: disable=too-many-statements:
    def test_chair_behavior(self):
        meeting = Meeting("nick", "channel", "network")
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick"]
        assert meeting.nicks == {"nick": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is False
        assert meeting.is_chair("yyy") is False
        assert meeting.is_chair("zzz") is False

        meeting.add_chair("yyy")
        assert meeting.founder == "nick"
        assert meeting.chair == "yyy"
        assert meeting.chairs == ["nick", "yyy"]
        assert meeting.nicks == {"nick": 0, "yyy": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is False
        assert meeting.is_chair("yyy") is True
        assert meeting.is_chair("zzz") is False

        meeting.add_chair("xxx", primary=False)
        assert meeting.founder == "nick"
        assert meeting.chair == "yyy"
        assert meeting.chairs == ["nick", "xxx", "yyy"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is True
        assert meeting.is_chair("zzz") is False

        meeting.add_chair("nick")
        assert meeting.founder == "nick"
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick", "xxx", "yyy"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is True
        assert meeting.is_chair("zzz") is False

        meeting.add_chair("zzz")
        assert meeting.founder == "nick"
        assert meeting.chair == "zzz"
        assert meeting.chairs == ["nick", "xxx", "yyy", "zzz"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0, "zzz": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is True
        assert meeting.is_chair("zzz") is True

        meeting.remove_chair("yyy")
        assert meeting.founder == "nick"
        assert meeting.chair == "zzz"
        assert meeting.chairs == ["nick", "xxx", "zzz"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0, "zzz": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is False
        assert meeting.is_chair("zzz") is True

        meeting.remove_chair("nick")  # you can't remove the founder
        assert meeting.founder == "nick"
        assert meeting.chair == "zzz"
        assert meeting.chairs == ["nick", "xxx", "zzz"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0, "zzz": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is False
        assert meeting.is_chair("zzz") is True

        meeting.remove_chair("zzz")  # removing the primary chair makes the founder the primary
        assert meeting.founder == "nick"
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick", "xxx"]
        assert meeting.nicks == {"nick": 0, "xxx": 0, "yyy": 0, "zzz": 0}
        assert meeting.is_chair("nick") is True
        assert meeting.is_chair("xxx") is True
        assert meeting.is_chair("yyy") is False
        assert meeting.is_chair("zzz") is False

    def test_track_nick(self):
        meeting = Meeting("nick", "channel", "network")
        meeting.track_nick("xxx")
        assert meeting.nicks["xxx"] == 1
        meeting.track_nick("yyy", messages=0)
        assert meeting.nicks["yyy"] == 0
        meeting.track_nick("nick")
        assert meeting.nicks["nick"] == 1
        meeting.track_nick("nick", messages=4)
        assert meeting.nicks["nick"] == 5

    def test_track_message_non_action(self):
        message = Message("nick", "channel", "network", "Hello, world")
        meeting = Meeting("n", "c", "n")
        tracked = meeting.track_message(message)
        assert meeting.nicks["nick"] == 1
        assert tracked in meeting.messages
        assert tracked.sender == "nick"
        assert tracked.payload == "Hello, world"
        assert tracked.action is False

    def test_track_message_action(self):
        # Trying to replicate "^AACTION waves goodbye^A" as in the Wikipedia article
        # See "DCC CHAT" under: https://en.wikipedia.org/wiki/Client-to-client_protocol
        message = Message("nick", "channel", "network", "\x01ACTION waves goodbye\x01")
        meeting = Meeting("n", "c", "n")
        tracked = meeting.track_message(message)
        assert meeting.nicks["nick"] == 1
        assert tracked in meeting.messages
        assert tracked.id is not None
        assert tracked.sender == "nick"
        assert tracked.payload == "waves goodbye"
        assert tracked.action is True

    def test_track_event_no_attributes(self):
        meeting = Meeting("n", "c", "n")
        timestamp = MagicMock()
        message = MagicMock(timestamp=timestamp)
        tracked = meeting.track_event(event_type=EventType.LURK, message=message)
        assert tracked in meeting.events
        assert tracked.id is not None
        assert tracked.event_type == EventType.LURK
        assert tracked.message is message
        assert tracked.timestamp is timestamp
        assert tracked.attributes == {}

    def test_track_event_with_attributes(self):
        meeting = Meeting("n", "c", "n")
        timestamp = MagicMock()
        message = MagicMock(timestamp=timestamp)
        tracked = meeting.track_event(event_type=EventType.LURK, message=message, one="ONE", two="222")
        assert tracked in meeting.events
        assert tracked.id is not None
        assert tracked.event_type == EventType.LURK
        assert tracked.message is message
        assert tracked.timestamp is timestamp
        assert tracked.attributes == {"one": "ONE", "two": "222"}

    def test_pop_event(self):
        meeting = Meeting("n", "c", "n")
        timestamp = MagicMock()
        message = MagicMock(timestamp=timestamp)
        tracked = meeting.track_event(event_type=EventType.LURK, message=message)
        assert tracked in meeting.events
        assert meeting.pop_event() is tracked
        assert meeting.events == []
        assert meeting.pop_event() is None
