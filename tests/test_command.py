# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, patch

import pytest

from hcoopmeetbotlogic.command import dispatch, is_startmeeting, list_commands


def run_dispatch(payload, operation, operand, method):
    meeting = MagicMock()
    message = MagicMock(payload=payload)
    method.reset_mock()  # so we can test same method with different scenarios
    dispatch(meeting, message)
    method.assert_called_once_with(meeting, operation, operand, message)


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
            "#meetingname",
            "#meetingtopic",
            "#nick",
            "#reject",
            "#rejected",
            "#startmeeting",
            "#topic",
            "#unchair",
            "#undo",
        ]

    @pytest.mark.parametrize(
        "message,expected",
        [
            pytest.param("#startmeeting", True),
            pytest.param(" #startmeeting", True),
            pytest.param("\t#startmeeting", True),
            pytest.param(" \t #startmeeting  extra stuff ", True),
            pytest.param("startmeeting", False),
            pytest.param("# startmeeting", False),
            pytest.param("#endmeeting", False),
            pytest.param("arbitrary message", False),
            pytest.param("", False),
            pytest.param("   ", False),
        ],
    )
    def test_startmeeting(self, message, expected):
        assert is_startmeeting(message=MagicMock(payload=message)) is expected

    # noinspection PyTypeChecker
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
    def test_dispatch_link(self, dispatcher, protocol):
        url = "%s://whatever" % protocol
        run_dispatch(url, "link", url, dispatcher.do_link)

    # noinspection PyTypeChecker
    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_targets(self, dispatcher):
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

    # noinspection PyTypeChecker
    @patch("hcoopmeetbotlogic.command._DISPATCHER")
    def test_dispatch_variations(self, dispatcher):
        run_dispatch(" #startmeeting", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch("\t#startmeeting", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch("#startmeeting   ", "startmeeting", "", dispatcher.do_startmeeting)
        run_dispatch(" #idea     some stuff    ", "idea", "some stuff", dispatcher.do_idea)
