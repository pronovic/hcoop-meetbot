# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import os
from datetime import datetime
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from hcoopmeetbotlogic.location import Location, Locations
from hcoopmeetbotlogic.meeting import EventType, TrackedEvent, TrackedMessage
from hcoopmeetbotlogic.writer import _LogMessage, write_meeting

EXPECTED_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/log.expected")
EXPECTED_MINUTES = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/minutes.expected")

TIMESTAMP = datetime(2021, 3, 7, 13, 14, 0)
START_TIME = datetime(2021, 4, 13, 2, 6, 12)
END_TIME = datetime(2021, 5, 19, 23, 2)


def _contents(path: str) -> str:
    """Get contents of a file for comparison."""
    with open(path, "r") as out:
        return out.read()


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
            + '</span><span class="topicline"><span><span>'
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
            + '</span><span class="cmdline"><span><span>'
            + operand
            + "</span></span></span></span>"
        )

    # pylint: disable=line-too-long:
    def test_highlights(self, config, message):
        message.action = False
        message.payload = "this is some stuff for highlight1: and more for highlight2: here and an https://url"
        result = _LogMessage.for_message(config, message)
        assert "%s" % result.id == '<a name="id"/>'
        assert "%s" % result.timestamp == '<span class="tm">13:14:00</span>'
        assert "%s" % result.nick == '<span class="nk">&lt;nick&gt;</span>'
        assert (
            "%s" % result.content
            == '<span><span>this is some stuff for </span><span class="hi">highlight1:</span><span> and more for </span><span class="hi">highlight2:</span><span> here and an https://url</span></span>'
        )

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
        # The goal here is to prove that rendering is wired up properly and that
        # files are written as expected.  We don't verify every different rendering
        # scenario - there are other tests that are intended to test the underlying
        # implementation at that level of detail.
        with TemporaryDirectory() as temp:
            log = Location(path=os.path.join(temp, "log.expected"), url="http://")
            minutes = Location(path=os.path.join(temp, "minutes.expected"), url="http://")
            locations = Locations(log=log, minutes=minutes)
            derive_locations.return_value = locations
            config = MagicMock(timezone="UTC")
            meeting = MagicMock()
            meeting.name = "#hcoop"
            meeting.start_time = START_TIME
            meeting.end_time = END_TIME
            meeting.founder = "founder"
            meeting.nicks = {"someone": "333"}
            meeting.messages = [TrackedMessage(id="id1", action=False, sender="nick", timestamp=TIMESTAMP, payload="stuff")]
            meeting.events = [
                TrackedEvent(
                    id="id2",
                    event_type=EventType.ACTION,
                    timestamp=TIMESTAMP,
                    message=meeting.messages[0],
                    attributes={"text": "someone will do something"},
                )
            ]
            assert write_meeting(config, meeting) is locations
            derive_locations.assert_called_once_with(config, meeting)
            print(_contents(minutes.path))
            assert _contents(log.path) == _contents(EXPECTED_LOG)
            assert _contents(minutes.path) == _contents(EXPECTED_MINUTES)
