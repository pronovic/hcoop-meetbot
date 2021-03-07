# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from pendulum import datetime, now

from hcoopmeetbotlogic.interface import Message
from hcoopmeetbotlogic.meeting import Meeting, TrackedMessage


class TestTrackedMessage:
    def test_constructor(self):
        before = now()
        message = TrackedMessage("sender", "payload", False)
        assert message.sender == "sender"
        assert message.payload == "payload"
        assert message.action is False
        assert message.timestamp >= before


class TestMeeting:
    def test_constructor(self):
        before = now()
        meeting = Meeting("nick", "channel", "network")
        assert meeting.id is not None
        assert meeting.founder == "nick"
        assert meeting.channel == "channel"
        assert meeting.network == "network"
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick"]
        assert meeting.start_time >= before
        assert meeting.end_time is None
        assert meeting.messages == []
        assert meeting.key() == "channel/network"
        assert meeting.active() is True

    def test_meeting_key(self):
        assert Meeting.meeting_key("channel", "network") == "channel/network"

    def test_mark_completed(self):
        meeting = Meeting("nick", "channel", "network")
        meeting.mark_completed()
        assert meeting.active() is False
        assert meeting.end_time >= meeting.start_time

    def test_add_chair(self):
        meeting = Meeting("nick", "channel", "network")
        meeting.add_chair("yyy")
        assert meeting.founder == "nick"
        assert meeting.chair == "yyy"
        assert meeting.chairs == ["nick", "yyy"]
        meeting.add_chair("xxx", primary=False)
        assert meeting.founder == "nick"
        assert meeting.chair == "yyy"
        assert meeting.chairs == ["nick", "xxx", "yyy"]
        meeting.add_chair("nick")
        assert meeting.founder == "nick"
        assert meeting.chair == "nick"
        assert meeting.chairs == ["nick", "xxx", "yyy"]

    def test_track_message_non_action(self):
        message = Message("nick", "channel", "network", "Hello, world")
        meeting = Meeting("n", "c", "n")
        tracked = meeting.track_message(message)
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
        assert tracked in meeting.messages
        assert tracked.sender == "nick"
        assert tracked.payload == "waves goodbye"
        assert tracked.action is True

    def test_display_name(self):
        meeting = Meeting("n", "c", "n")
        meeting.start_time = datetime(2021, 3, 7, 13, 14, 0)  # in UTC by default
        assert meeting.display_name() == "c/n@2021-03-07T13:14+0000"
