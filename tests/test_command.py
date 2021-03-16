# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from hcoopmeetbotlogic.command import CommandDispatcher, dispatch, is_startmeeting, list_commands
from hcoopmeetbotlogic.meeting import EventType


def run_dispatch(payload, operation, operand, method):
    meeting = MagicMock()
    context = MagicMock()
    message = MagicMock(payload=payload)
    method.reset_mock()  # so we can test same method with different scenarios
    dispatch(meeting, context, message)
    method.assert_called_once_with(meeting, context, operation, operand, message)


class TestFunctions:
    def test_list_commands(self):
        assert list_commands() == [
            "#accept",
            "#accepted",
            "#action",
            "#agree",
            "#agreed",
            "#chair",
            "#endmeeting",
            "#fail",
            "#failed",
            "#help",
            "#idea",
            "#info",
            "#link",
            "#lurk",
            "#meetingname",
            "#meetingtopic",
            "#nick",
            "#reject",
            "#rejected",
            "#save",
            "#startmeeting",
            "#topic",
            "#unchair",
            "#undo",
            "#unlurk",
        ]

    @pytest.mark.parametrize(
        "message,expected",
        [
            pytest.param("#startmeeting", True, id="normal"),
            pytest.param(" #startmeeting", True, id="leading spaces"),
            pytest.param("\t#startmeeting", True, id="leading tab"),
            pytest.param(" \t #startmeeting  extra stuff ", True, id="extra stuff"),
            pytest.param("startmeeting", False, id="no leading #"),
            pytest.param("# startmeeting", False, id="space after #"),
            pytest.param("#endmeeting", False, id="wrong command"),
            pytest.param("arbitrary message", False, id="arbitrary message"),
            pytest.param("", False, id="empty"),
            pytest.param("   ", False, id="all whitespace"),
        ],
    )
    def test_startmeeting(self, message, expected):
        assert is_startmeeting(message=MagicMock(payload=message)) is expected

    @pytest.mark.parametrize(
        "protocol",
        [
            pytest.param("http"),
            pytest.param("https"),
            pytest.param("irc"),
            pytest.param("ftp"),
            pytest.param("mailto"),
            pytest.param("ssh"),
        ],
    )
    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_valid_link(self, dispatcher, protocol):
        url = "%s://whatever" % protocol
        run_dispatch(url, "link", url, dispatcher.do_link)

    @pytest.mark.parametrize(
        "protocol",
        [
            pytest.param("", id="empty"),
            pytest.param("bogus"),
        ],
    )
    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_invalid_link(self, dispatcher, protocol):
        url = "%s://whatever" % protocol
        meeting = MagicMock()
        context = MagicMock()
        message = MagicMock(payload=url)
        dispatch(meeting, context, message)
        dispatcher.do_link.assert_not_called()

    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_valid_command(self, dispatcher):
        run_dispatch("#startmeeting", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch("#endmeeting", "endmeeting", "", dispatcher.do_endmeeting)
        run_dispatch("#topic some stuff", "topic", "some stuff", dispatcher.do_topic)
        run_dispatch("#meetingtopic some stuff", "meetingtopic", "some stuff", dispatcher.do_meetingtopic)
        run_dispatch("#accepted", "accepted", "", dispatcher.do_accepted)
        run_dispatch("#accept", "accept", "", dispatcher.do_accept)
        run_dispatch("#agree", "agree", "", dispatcher.do_agree)
        run_dispatch("#agreed", "agreed", "", dispatcher.do_agreed)
        run_dispatch("#failed", "failed", "", dispatcher.do_failed)
        run_dispatch("#fail", "fail", "", dispatcher.do_fail)
        run_dispatch("#reject", "reject", "", dispatcher.do_reject)
        run_dispatch("#rejected", "rejected", "", dispatcher.do_rejected)
        run_dispatch("#chair name", "chair", "name", dispatcher.do_chair)
        run_dispatch("#unchair name", "unchair", "name", dispatcher.do_unchair)
        run_dispatch("#undo", "undo", "", dispatcher.do_undo)
        run_dispatch("#meetingname name", "meetingname", "name", dispatcher.do_meetingname)
        run_dispatch("#action some stuff", "action", "some stuff", dispatcher.do_action)
        run_dispatch("#nick name", "nick", "name", dispatcher.do_nick)
        run_dispatch("#info some stuff", "info", "some stuff", dispatcher.do_info)
        run_dispatch("#idea some stuff", "idea", "some stuff", dispatcher.do_idea)
        run_dispatch("#help some stuff", "help", "some stuff", dispatcher.do_help)
        run_dispatch("#link http://whatever", "link", "http://whatever", dispatcher.do_link)

    @patch("hcoopmeetbotlogic.command.hasattr")
    @patch("hcoopmeetbotlogic.command.getattr")
    def test_dispatch_invalid_command(self, getattr, hasattr):  # pylint: disable=redefined-builtin:
        meeting = MagicMock()
        context = MagicMock()
        message = MagicMock(payload="#bogus")
        hasattr.return_value = False
        dispatch(meeting, context, message)
        getattr.assert_not_called()

    # noinspection PyTypeChecker
    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_command_variations(self, dispatcher):
        run_dispatch(" #startmeeting", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch("\t#startmeeting", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch("#startmeeting   ", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch(" #idea     some stuff    ", "idea", "some stuff", dispatcher.do_idea)


# pylint: disable=too-many-public-methods:
class TestCommandDispatcher:
    @pytest.fixture
    def dispatcher(self):
        return CommandDispatcher()

    @pytest.fixture
    def meeting(self):
        return MagicMock()

    @pytest.fixture
    def context(self):
        return MagicMock()

    @pytest.fixture
    def message(self):
        return MagicMock(sender="nick")

    @patch("hcoopmeetbotlogic.command.formatdate")
    @patch("hcoopmeetbotlogic.command.config")
    def test_startmeeting_as_chair(self, config, formatdate, dispatcher, meeting, context, message):
        meeting.active = False
        meeting.original_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = True
        meeting.chairs = ["x", "y"]
        meeting.start_time = datetime(2021, 3, 7, 13, 14, 0)
        config.return_value = MagicMock(timezone="America/Chicago")
        formatdate.return_value = "11111"
        context.get_topic = MagicMock(return_value="original")
        dispatcher.do_startmeeting(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.START_MEETING, message)
        context.set_topic("b")
        context.send_reply.assert_has_calls(
            [
                call("Meeting started at 11111"),
                call("Current chairs: x, y"),
                call("Useful commands: #action #agreed #help #info #idea #link #topic"),
            ]
        )
        assert meeting.original_topic == "original"
        assert meeting.meeting_topic == "b"
        formatdate.assert_called_once_with(timestamp=meeting.start_time, zone="America/Chicago")

    def test_startmeeting_as_chair_duplicated(self, dispatcher, meeting, context, message):
        meeting.active = True
        meeting.original_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = True
        dispatcher.do_startmeeting(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.set_topic.assert_not_called()
        context.sent_reply.assert_not_called()
        assert meeting.active is True
        assert meeting.original_topic is None
        assert meeting.meeting_topic is None

    def test_startmeeting_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.active = False
        meeting.original_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = False
        dispatcher.do_startmeeting(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.set_topic.assert_not_called()
        context.sent_reply.assert_not_called()
        assert meeting.active is False
        assert meeting.original_topic is None
        assert meeting.meeting_topic is None

    @patch("hcoopmeetbotlogic.command.formatdate")
    @patch("hcoopmeetbotlogic.command.now")
    @patch("hcoopmeetbotlogic.command.config")
    @patch("hcoopmeetbotlogic.command.write_meeting")
    def test_endmeeting_as_chair(self, write_meeting, config, now, formatdate, dispatcher, meeting, context, message):
        meeting.end_time = None
        meeting.active = None
        meeting.original_topic = "original"
        config.return_value = MagicMock(timezone="America/Chicago")
        formatdate.return_value = "11111"
        now.return_value = datetime(2021, 3, 7, 13, 14, 0)
        meeting.is_chair.return_value = True
        write_meeting.return_value = MagicMock()
        write_meeting.return_value.log = MagicMock(url="logurl")
        write_meeting.return_value.minutes = MagicMock(url="minutesurl")
        dispatcher.do_endmeeting(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.END_MEETING, message)
        write_meeting.assert_called_once_with(config=config.return_value, meeting=meeting)
        context.send_reply.assert_has_calls([call("Meeting ended at 11111"), call("Raw log: logurl"), call("Minutes: minutesurl")])
        context.set_topic.assert_called_once_with("original")
        formatdate.assert_called_once_with(timestamp=now.return_value, zone="America/Chicago")
        assert meeting.end_time is now.return_value
        assert meeting.active is False

    @patch("hcoopmeetbotlogic.command.write_meeting")
    def test_endmeeting_as_not_chair(self, write_meeting, dispatcher, meeting, context, message):
        meeting.end_time = None
        meeting.active = None
        meeting.is_chair.return_value = False
        dispatcher.do_endmeeting(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        write_meeting.assert_not_called()
        context.set_topic.assert_not_called()
        context.send_reply.assert_not_called()
        assert meeting.end_time is None
        assert meeting.active is None

    @patch("hcoopmeetbotlogic.command.config")
    @patch("hcoopmeetbotlogic.command.write_meeting")
    def test_save_as_chair(self, write_meeting, config, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        config.return_value = MagicMock()
        write_meeting.return_value = MagicMock()
        write_meeting.return_value.log = MagicMock(url="logurl")
        write_meeting.return_value.minutes = MagicMock(url="minutesurl")
        dispatcher.do_save(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.SAVE_MEETING, message)
        write_meeting.assert_called_once_with(config=config.return_value, meeting=meeting)
        context.send_reply.assert_has_calls([call("Meeting saved"), call("Raw log: logurl"), call("Minutes: minutesurl")])

    @patch("hcoopmeetbotlogic.command.write_meeting")
    def test_save_as_not_chair(self, write_meeting, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_save(meeting, context, "a", "b", message)
        write_meeting.assert_not_called()
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_lurk_as_chair(self, dispatcher, meeting, context, message):
        meeting.lurk = None
        meeting.is_chair.return_value = True
        dispatcher.do_lurk(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.LURK, message)
        assert meeting.lurk is True

    def test_lurk_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.lurk = None
        meeting.is_chair.return_value = False
        dispatcher.do_lurk(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        assert meeting.lurk is None

    def test_unlurk_as_chair(self, dispatcher, meeting, context, message):
        meeting.lurk = None
        meeting.is_chair.return_value = True
        dispatcher.do_unlurk(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.UNLURK, message)
        assert meeting.lurk is False

    def test_unlurk_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.lurk = None
        meeting.is_chair.return_value = False
        dispatcher.do_unlurk(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        assert meeting.lurk is None

    def test_meetingtopic_as_chair_empty(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.meeting_topic = None
        meeting.display_name = MagicMock(return_value="name")
        meeting.is_chair.return_value = True
        dispatcher.do_meetingtopic(meeting, context, "a", "", message)
        meeting.track_event.assert_called_once_with(EventType.MEETING_TOPIC, message, meetingtopic="")
        context.set_topic.assert_called_once_with("name")
        assert meeting.meeting_topic == ""

    def test_meetingtopic_as_chair_not_empty(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = True
        dispatcher.do_meetingtopic(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.MEETING_TOPIC, message, meetingtopic="b")
        context.set_topic.assert_called_once_with("b")
        assert meeting.meeting_topic == "b"

    def test_meetingtopic_as_chair_with_topic(self, dispatcher, meeting, context, message):
        meeting.current_topic = "x"
        meeting.meeting_topic = None
        meeting.is_chair.return_value = True
        dispatcher.do_meetingtopic(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.MEETING_TOPIC, message, meetingtopic="b")
        context.set_topic.assert_called_once_with("x (Meeting topic: b)")
        assert meeting.meeting_topic == "b"

    def test_meetingtopic_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = False
        dispatcher.do_meetingtopic(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.set_topic.assert_not_called()
        assert meeting.meeting_topic is None

    def test_topic_as_chair_empty(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.meeting_topic = None
        meeting.display_name = MagicMock(return_value="name")
        meeting.is_chair.return_value = True
        dispatcher.do_topic(meeting, context, "a", "", message)
        meeting.track_event.assert_called_once_with(EventType.CURRENT_TOPIC, message, topic="")
        context.set_topic.assert_called_once_with("name")
        assert meeting.current_topic == ""

    def test_topic_as_chair_not_empty(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.meeting_topic = None
        meeting.is_chair.return_value = True
        dispatcher.do_topic(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.CURRENT_TOPIC, message, topic="b")
        context.set_topic.assert_called_once_with("b")
        assert meeting.current_topic == "b"

    def test_topic_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.current_topic = None
        meeting.is_chair.return_value = False
        dispatcher.do_topic(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.set_topic.assert_not_called()
        assert meeting.current_topic is None

    def test_chair_as_chair_empty(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_chair(meeting, context, "a", "", message)
        meeting.track_event.assert_not_called()
        meeting.add_chair.assert_not_called()
        context.send_reply.assert_not_called()

    def test_chair_as_chair_single(self, dispatcher, meeting, context, message):
        meeting.chairs = ["x", "y"]
        meeting.is_chair.return_value = True
        dispatcher.do_chair(meeting, context, "a", "one", message)
        meeting.track_event.assert_called_once_with(EventType.ADD_CHAIR, message, chairs=["one"])
        meeting.add_chair.assert_called_once_with("one", primary=False)
        context.send_reply.assert_called_once_with("Current chairs: x, y")

    def test_chair_as_chair_multiple(self, dispatcher, meeting, context, message):
        meeting.chairs = ["x", "y"]
        meeting.is_chair.return_value = True
        dispatcher.do_chair(meeting, context, "a", "one, two three   four five, six", message)
        meeting.track_event.assert_called_once_with(
            EventType.ADD_CHAIR, message, chairs=["one", "two", "three", "four", "five", "six"]
        )
        meeting.add_chair.assert_has_calls(
            [
                call("one", primary=False),
                call("two", primary=False),
                call("three", primary=False),
                call("four", primary=False),
                call("five", primary=False),
                call("six", primary=False),
            ]
        )
        context.send_reply.assert_called_once_with("Current chairs: x, y")

    def test_chair_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_chair(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        meeting.add_chair.assert_not_called()
        context.send_reply.assert_not_called()

    def test_unchair_as_chair_empty(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_unchair(meeting, context, "a", "", message)
        meeting.track_event.assert_not_called()
        meeting.remove_chair.assert_not_called()
        context.send_reply.assert_not_called()

    def test_unchair_as_chair_single(self, dispatcher, meeting, context, message):
        meeting.chairs = ["x", "y"]
        meeting.is_chair.return_value = True
        dispatcher.do_unchair(meeting, context, "a", "one", message)
        meeting.track_event.assert_called_once_with(EventType.REMOVE_CHAIR, message, chairs=["one"])
        meeting.remove_chair.assert_called_once_with("one")
        context.send_reply.assert_called_once_with("Current chairs: x, y")

    def test_unchair_as_chair_multiple(self, dispatcher, meeting, context, message):
        meeting.chairs = ["x", "y"]
        meeting.is_chair.return_value = True
        dispatcher.do_unchair(meeting, context, "a", "one, two three   four five, six", message)
        meeting.track_event.assert_called_once_with(
            EventType.REMOVE_CHAIR, message, chairs=["one", "two", "three", "four", "five", "six"]
        )
        meeting.remove_chair.assert_has_calls([call("one"), call("two"), call("three"), call("four"), call("five"), call("six")])
        context.send_reply.assert_called_once_with("Current chairs: x, y")

    def test_unchair_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_unchair(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        meeting.remove_chair.assert_not_called()
        context.send_reply.assert_not_called()

    def test_nick_empty(self, dispatcher, meeting, context, message):
        dispatcher.do_nick(meeting, context, "a", "", message)
        meeting.track_event.assert_not_called()
        meeting.track_nick.assert_not_called()
        context.send_reply.assert_not_called()

    def test_nick_single(self, dispatcher, meeting, context, message):
        meeting.nicks = {"x": 99, "y": 22}
        dispatcher.do_nick(meeting, context, "a", "one", message)
        meeting.track_event.assert_called_once_with(EventType.TRACK_NICK, message, nicks=["one"])
        meeting.track_nick.assert_called_once_with("one", messages=0)
        context.send_reply.assert_called_once_with("Current nicks: x, y")

    def test_nick_multiple(self, dispatcher, meeting, context, message):
        meeting.nicks = {"x": 99, "y": 22}
        dispatcher.do_nick(meeting, context, "a", "one, two three   four five, six", message)
        meeting.track_event.assert_called_once_with(
            EventType.TRACK_NICK, message, nicks=["one", "two", "three", "four", "five", "six"]
        )
        meeting.track_nick.assert_has_calls(
            [
                call("one", messages=0),
                call("two", messages=0),
                call("three", messages=0),
                call("four", messages=0),
                call("five", messages=0),
                call("six", messages=0),
            ]
        )
        context.send_reply.assert_called_once_with("Current nicks: x, y")

    def test_undo_as_chair_no_events(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        meeting.pop_event.return_value = None
        dispatcher.do_undo(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_undo_as_chair_with_events(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        meeting.pop_event.return_value = MagicMock(id="theid")
        meeting.pop_event.return_value.display_name = MagicMock(return_value="theevent")
        dispatcher.do_undo(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.UNDO, message, id="theid")
        context.send_reply.assert_called_once_with("Removed event: theevent")

    def test_undo_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_undo(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        meeting.pop_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_meetingname_as_chair(self, dispatcher, meeting, context, message):
        meeting.name = None
        meeting.is_chair.return_value = True
        dispatcher.do_meetingname(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.MEETING_NAME, message, meetingname="b")
        context.send_reply.assert_called_once_with("Meeting name set to: b")
        assert meeting.name == "b"

    def test_meetingname_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.name = None
        meeting.is_chair.return_value = False
        dispatcher.do_meetingname(meeting, context, "a", "b", message)
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()
        assert meeting.name is None

    def test_accepted_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_accepted(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.ACCEPTED, message, text="b")
        context.send_reply.assert_not_called()

    def test_accepted_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_accepted(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_accept_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_accept(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.ACCEPTED, message, text="b")
        context.send_reply.assert_not_called()

    def test_accept_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_accept(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_agree_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_agree(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.ACCEPTED, message, text="b")
        context.send_reply.assert_not_called()

    def test_agree_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_agree(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_agreed_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_agreed(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.ACCEPTED, message, text="b")
        context.send_reply.assert_not_called()

    def test_agreed_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_agreed(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_failed_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_failed(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.FAILED, message, text="b")
        context.send_reply.assert_not_called()

    def test_failed_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_failed(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_fail_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_fail(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.FAILED, message, text="b")
        context.send_reply.assert_not_called()

    def test_fail_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_fail(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_reject_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_reject(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.FAILED, message, text="b")
        context.send_reply.assert_not_called()

    def test_reject_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_reject(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_rejected_as_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = True
        dispatcher.do_rejected(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_called_once_with(EventType.FAILED, message, text="b")
        context.send_reply.assert_not_called()

    def test_rejected_as_not_chair(self, dispatcher, meeting, context, message):
        meeting.is_chair.return_value = False
        dispatcher.do_rejected(meeting, context, "a", "b", message)
        meeting.is_chair.assert_called_once_with("nick")  # message.sender
        meeting.track_event.assert_not_called()
        context.send_reply.assert_not_called()

    def test_action(self, dispatcher, meeting, context, message):
        dispatcher.do_action(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.ACTION, message, text="b")
        context.send_reply.assert_not_called()

    def test_info(self, dispatcher, meeting, context, message):
        dispatcher.do_info(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.INFO, message, text="b")
        context.send_reply.assert_not_called()

    def test_idea(self, dispatcher, meeting, context, message):
        dispatcher.do_idea(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.IDEA, message, text="b")
        context.send_reply.assert_not_called()

    def test_help(self, dispatcher, meeting, context, message):
        dispatcher.do_help(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.HELP, message, text="b")
        context.send_reply.assert_not_called()

    def test_link(self, dispatcher, meeting, context, message):
        dispatcher.do_link(meeting, context, "a", "b", message)
        meeting.track_event.assert_called_once_with(EventType.LINK, message, url="b")
        context.send_reply.assert_not_called()
