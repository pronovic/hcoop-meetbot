# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import os
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from hcoopmeetbotlogic.interface import Message
from hcoopmeetbotlogic.location import Location, Locations
from hcoopmeetbotlogic.meeting import EventType, Meeting, VotingAction
from hcoopmeetbotlogic.writer import _LogMessage, write_meeting

EXPECTED_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/log.html")
EXPECTED_MINUTES = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/minutes.html")

TIMESTAMP = datetime(2021, 3, 7, 13, 14, 0)
START_TIME = datetime(2021, 4, 13, 2, 6, 12)
END_TIME = datetime(2021, 5, 19, 23, 2)


def _contents(path: str) -> str:
    """Get contents of a file for comparison."""
    with open(path, "r") as out:
        return out.read()


def _time(seconds: int) -> datetime:
    """Generate a timestamp relative to START_TIME"""
    return START_TIME + timedelta(seconds=seconds)


def _message(identifier: int, nick: str, payload: str, seconds: int) -> Message:
    """Generate a mocked message with some values"""
    return MagicMock(id="id-%d" % identifier, nick=nick, payload=payload, timestamp=_time(seconds))


def _meeting() -> Meeting:
    """Generate a semi-realistic meeting that can be used for unit tests"""

    # Initialize the meeting
    meeting = Meeting(founder="pronovic", channel="#hcoop", network="network")

    # this gets us some data in the attendees section without having to add tons of messages
    meeting.track_nick("unknown_lamer", 13)
    meeting.track_nick("layline", 32)
    meeting.track_nick("bhkl", 3)

    # Start the meeting
    meeting.active = True
    meeting.start_time = START_TIME
    tracked = meeting.track_message(message=_message(0, "pronovic", "#startmeeting", 0))
    meeting.track_event(event_type=EventType.START_MEETING, message=tracked)

    # these messages and events will be associated with the prologue, because no topic has been set yet
    tracked = meeting.track_message(message=_message(1, "pronovic", "Hello everyone, is it ok to get started?", 32))
    tracked = meeting.track_message(message=_message(2, "unknown_lamer", "Yeah, let's do it", 97))
    tracked = meeting.track_message(message=_message(3, "pronovic", "#link https://whatver/agenda.html", 123))
    meeting.track_event(event_type=EventType.LINK, message=tracked, operand="https://whatver/agenda.html")

    # these messages and events are associated with the first topic
    tracked = meeting.track_message(message=_message(4, "pronovic", "#topic The first topic", 199))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The first topic")
    tracked = meeting.track_message(message=_message(5, "pronovic", "Does anyone have any discussion?", 231))
    tracked = meeting.track_message(message=_message(6, "layline", "Is this important?", 232))
    tracked = meeting.track_message(message=_message(7, "unknown_lamer", "Yes it is", 299))
    tracked = meeting.track_message(message=_message(8, "pronovic", "#info moving on then", 305))
    meeting.track_event(event_type=EventType.INFO, message=tracked, operand="moving on then")

    # these messages and events are associated with the second topic
    tracked = meeting.track_message(message=_message(9, "pronovic", "#topic The second topic", 332))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The second topic")
    tracked = meeting.track_message(message=_message(10, "layline", "\x01unknown_lamer: I need you for this action\x01", 334))
    tracked = meeting.track_message(message=_message(11, "pronovic", "#action unknown_lamer will work with layline on this", 401))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="unknown_lamer will work with layline on this")

    # these messages and events are associated with the third topic
    tracked = meeting.track_message(message=_message(12, "pronovic", "#topic The third topic", 407))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The third topic")
    tracked = meeting.track_message(message=_message(13, "pronovic", "#idea we should improve MeetBot", 414))
    meeting.track_event(event_type=EventType.IDEA, message=tracked, operand="we should improve MeetBot")
    tracked = meeting.track_message(message=_message(14, "pronovic", "I'll just take this one myself", 435))
    tracked = meeting.track_message(message=_message(15, "pronovic", "#action pronovic will deal with it", 449))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="pronovic will deal with it")

    # these messages and events are associated with the final topic
    tracked = meeting.track_message(message=_message(12, "pronovic", "#topic Cross-site Scripting", 453))
    tracked = meeting.track_message(message=_message(15, "pronovic", "#action <script>alert('malicious')</script>", 497))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="<script>alert('malicious')</script>")
    tracked = meeting.track_message(message=_message(12, "pronovic", "#motion the motion", 502))
    meeting.track_event(event_type=EventType.MOTION, message=tracked, operand="the motion")
    tracked = meeting.track_message(message=_message(12, "pronovic", "#vote +1", 553))
    meeting.track_event(event_type=EventType.VOTE, message=tracked, operand=VotingAction.IN_FAVOR)

    # End the meeting
    tracked = meeting.track_message(message=_message(16, "pronovic", "#endmeeting", 567))
    meeting.track_event(event_type=EventType.END_MEETING, message=tracked)
    meeting.active = False
    meeting.end_time = END_TIME

    return meeting


class TestLogMessage:
    @pytest.fixture
    def config(self):
        return MagicMock(timezone="UTC")

    @pytest.fixture
    def message(self):
        return MagicMock(id="id", timestamp=TIMESTAMP, sender="nick")

    def test_simple_payload(self, config, message):
        message.action = False
        message.payload = "payload"
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert "%s" % result.content == "<span><span>payload</span></span>"

    def test_action_payload(self, config, message):
        message.action = True
        message.payload = "payload"
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nka">&lt;nick&gt;</span>'
        assert "%s" % result.content == '<span class="ac"><span><span>payload</span></span></span>'

    @pytest.mark.parametrize(
        "payload,operation,operand",
        [
            pytest.param("#topic thetopic", "#topic", "thetopic", id="empty"),
            pytest.param(" #topic thetopic", "#topic", "thetopic", id="leading spaces"),
            pytest.param("\t#topic thetopic", "#topic", "thetopic", id="leading tab"),
            pytest.param(" \t #topic  extra stuff ", "#topic", "extra stuff", id="extra stuff"),
        ],
    )
    def test_topic_payload(self, config, message, payload, operation, operand):
        message.action = False
        message.payload = payload
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert (
            "%s" % result.content
            == '<span><span class="topic">'
            + operation
            + ' </span><span class="topicline"><span><span>'
            + operand
            + "</span></span></span></span>"
        )

    @pytest.mark.parametrize(
        "payload,operation,operand",
        [
            pytest.param("#whatever context", "#whatever", "context", id="empty"),
            pytest.param(" #whatever context", "#whatever", "context", id="leading spaces"),
            pytest.param("\t#whatever context", "#whatever", "context", id="leading tab"),
            pytest.param(" \t #whatever  extra stuff ", "#whatever", "extra stuff", id="extra stuff"),
        ],
    )
    def test_command_payload(self, config, message, payload, operation, operand):
        message.action = False
        message.payload = payload
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert (
            "%s" % result.content
            == '<span><span class="cmd">'
            + operation
            + ' </span><span class="cmdline"><span><span>'
            + operand
            + "</span></span></span></span>"
        )

    def test_highlights(self, config, message):
        message.action = False
        message.payload = "nick: this is some stuff: yeah that stuff"
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert (
            "%s" % result.content == '<span><span class="hi">nick:</span><span> this is some stuff: yeah that stuff</span></span>'
        )

    def test_url(self, config, message):
        message.action = False
        message.payload = "http://whatever this should not be highlighted"
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert "%s" % result.content == "<span><span>http://whatever this should not be highlighted</span></span>"

    # we can generally expect Genshi to handle this stuff, so this is a spot-check
    # examples from: https://owasp.org/www-community/attacks/xss/
    @pytest.mark.parametrize(
        "payload,expected",
        [
            pytest.param("<script>alert('hello')</script>", "&lt;script&gt;alert('hello')&lt;/script&gt;", id="script tag"),
            pytest.param("<body onload=alert('test1')>", "&lt;body onload=alert('test1')&gt;", id="body onload"),
            pytest.param(
                '<img src="http://url.to.file.which/not.exist" onerror=alert(document.cookie);>',
                '&lt;img src="http://url.to.file.which/not.exist" onerror=alert(document.cookie);&gt;',
                id="onerror",
            ),
            pytest.param(
                "<b onmouseover=alert('Wufff!')>click me!</b>",
                "&lt;b onmouseover=alert('Wufff!')&gt;click me!&lt;/b&gt;",
                id="mouseover",
            ),
        ],
    )
    def test_cross_site_scripting(self, config, message, payload, expected):
        message.action = False
        message.payload = payload
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert "%s" % result.content == "<span><span>" + expected + "</span></span>"


class TestRendering:
    @patch("hcoopmeetbotlogic.writer.derive_locations")
    def test_write_meeting_wiring(self, derive_locations):
        # The goal here is to prove that rendering is wired up properly, the templates are
        # valid, and that files are written as expected.  We don't necessarily verify every
        # different scenario - there are other tests above that delve into some of the details.
        with TemporaryDirectory() as temp:
            log = Location(path=os.path.join(temp, "log.html"), url="http://")
            minutes = Location(path=os.path.join(temp, "minutes.html"), url="http://")
            locations = Locations(log=log, minutes=minutes)
            derive_locations.return_value = locations
            config = MagicMock(timezone="America/Chicago")
            meeting = _meeting()
            assert write_meeting(config, meeting) is locations
            print(_contents(minutes.path))
            derive_locations.assert_called_once_with(config, meeting)
            assert _contents(log.path) == _contents(EXPECTED_LOG)
            assert _contents(minutes.path) == _contents(EXPECTED_MINUTES)
