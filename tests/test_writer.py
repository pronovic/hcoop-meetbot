# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import os
from datetime import datetime
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from hcoopmeetbotlogic.config import OutputFormat
from hcoopmeetbotlogic.location import Location, Locations
from hcoopmeetbotlogic.meeting import Meeting
from hcoopmeetbotlogic.writer import _AliasMatcher, _LogMessage, write_meeting

from .testdata import contents, sample_meeting

EXPECTED_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/log.html")
EXPECTED_MINUTES = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/minutes.html")
TIMESTAMP = datetime(2021, 3, 7, 13, 14, 0)


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
            + "%s" % operation
            + ' </span><span class="topicline"><span><span>'
            + "%s" % operand
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
            + "%s" % operation
            + ' </span><span class="cmdline"><span><span>'
            + "%s" % operand
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
        assert "%s" % result.content == "<span><span>" + "%s" % expected + "</span></span>"


class TestRendering:
    @patch("hcoopmeetbotlogic.writer.DATE", "2001-02-03")
    @patch("hcoopmeetbotlogic.writer.VERSION", "1.2.3")
    @patch("hcoopmeetbotlogic.writer.derive_locations")
    def test_html_rendering(self, derive_locations):
        # The goal here is to prove that rendering is wired up properly, the templates are
        # valid, and that files are written as expected.  We don't necessarily verify every
        # different scenario - there are tests elsewhere that delve into some of the details.
        with TemporaryDirectory() as temp:
            raw_log = Location(path=os.path.join(temp, "log.json"), url="http://raw")
            formatted_log = Location(path=os.path.join(temp, "log.html"), url="http://log")
            formatted_minutes = Location(path=os.path.join(temp, "minutes.html"), url="http://minutes")
            locations = Locations(raw_log=raw_log, formatted_log=formatted_log, formatted_minutes=formatted_minutes)
            derive_locations.return_value = locations
            config = MagicMock(timezone="America/Chicago", output_format=OutputFormat.HTML)
            meeting = sample_meeting()
            assert write_meeting(config, meeting) is locations
            # print("\n" + contents(raw_log.path))
            # print("\n" + contents(formatted_log.path))
            # print("\n" + contents(formatted_minutes.path))
            derive_locations.assert_called_once_with(config, meeting)
            assert meeting == Meeting.from_json(contents(raw_log.path))  # raw log should exactly represent the meeting input
            assert contents(formatted_log.path) == contents(EXPECTED_LOG)
            assert contents(formatted_minutes.path) == contents(EXPECTED_MINUTES)


class TestAliasMatcher:
    @pytest.mark.parametrize(
        "identifier",
        [
            pytest.param("ken"),
            pytest.param("Ken"),
            pytest.param("Ken Pronovici"),
            pytest.param("k[n"),
            pytest.param("K[n"),
            pytest.param("K[n Pronovici"),
            pytest.param("[ken"),
            pytest.param("[Ken"),
            pytest.param("[Ken Pronovici"),
            pytest.param("ken]"),
            pytest.param("Ken]"),
            pytest.param("Ken Pronovici]"),
            pytest.param("[ken]"),
            pytest.param("[Ken]"),
            pytest.param("[Ken Pronovici]"),
        ],
    )
    def test_matches(self, identifier):

        match = []
        no_match = []

        # These should be considered a match because the identifier is found unambiguously
        match.append("%s" % identifier)
        match.append("%s got assigned a task" % identifier)
        match.append("assign that to %s please" % identifier)
        match.append("that task goes to %s" % identifier)
        match.append("hey %s: please take care of that" % identifier)
        match.append("an action item (%s)" % identifier)
        match.append("(%s) an action item" % identifier)

        # These should NOT be considered a match because the identifier has a prefix
        no_match.append("prefix%s" % identifier)
        no_match.append("prefix%s got assigned a task" % identifier)
        no_match.append("assign that to prefix%s please" % identifier)
        no_match.append("that task goes to prefix%s" % identifier)
        no_match.append("hey prefix%s: please take care of that" % identifier)
        no_match.append("an action item (prefix%s)" % identifier)
        no_match.append("(prefix%s) an action item" % identifier)

        # These should NOT be considered a match because the identifier has a suffix
        no_match.append("%ssuffix" % identifier)
        no_match.append("%ssuffix got assigned a task" % identifier)
        no_match.append("assign that to %ssuffix please" % identifier)
        no_match.append("that task goes to %ssuffix" % identifier)
        no_match.append("hey %ssuffix: please take care of that" % identifier)
        no_match.append("an action item (%ssuffix)" % identifier)
        no_match.append("(%ssuffix) an action item" % identifier)

        # These should NOT be considered a match because the identifier is embedded in another string
        no_match.append("prefix%ssuffix" % identifier)
        no_match.append("prefix%ssuffix got assigned a task" % identifier)
        no_match.append("assign that to prefix%ssuffix please" % identifier)
        no_match.append("that task goes to prefix%ssuffix" % identifier)
        no_match.append("hey prefix%ssuffix: please take care of that" % identifier)
        no_match.append("an action item (prefix%ssuffix)" % identifier)
        no_match.append("(prefix%ssuffix) an action item" % identifier)

        nick_matcher = _AliasMatcher(identifier, None)  # checks matching for nick
        alias_matcher = _AliasMatcher("bogus", identifier)  # checks matching for alias, since nick will never match

        for message in match:
            for testcase in [message, message.upper(), message.lower(), message.title()]:  # nicks/aliases are not case-sensitive
                if not nick_matcher.matches(testcase):
                    pytest.fail("nick '%s' not found in message '%s'" % (identifier, testcase))
                if not alias_matcher.matches(testcase):
                    pytest.fail("alias '%s' not found in message '%s'" % (identifier, testcase))

        for message in no_match:
            for testcase in [message, message.upper(), message.lower(), message.title()]:  # nicks/aliases are not case-sensitive
                if nick_matcher.matches(testcase):
                    pytest.fail("nick '%s' incorrectly found in message '%s'" % (identifier, testcase))
                if alias_matcher.matches(testcase):
                    pytest.fail("alias '%s' incorrectly found in message '%s'" % (identifier, testcase))
