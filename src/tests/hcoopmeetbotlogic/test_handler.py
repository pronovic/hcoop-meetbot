# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument,redefined-outer-name:

from unittest.mock import MagicMock, call, patch

import pytest

from hcoopmeetbotlogic.handler import (
    _send_reply,
    addchair,
    commands,
    configure,
    deletemeeting,
    irc_message,
    listmeetings,
    meetversion,
    outbound_message,
    recent,
    savemeetings,
)


@pytest.fixture
def context():
    context = MagicMock()
    context.send_reply = MagicMock()
    return context


class TestUtilities:
    @patch("hcoopmeetbotlogic.handler.logger")
    def test_send_reply(self, logger, context):
        stub = MagicMock()
        stub.debug = MagicMock()
        logger.return_value = stub
        _send_reply(context, "message")
        stub.debug.assert_called_once_with("message")
        context.send_reply.assert_called_once_with("message")


class TestConfig:
    @patch("hcoopmeetbotlogic.handler.set_config")
    @patch("hcoopmeetbotlogic.handler.set_logger")
    @patch("hcoopmeetbotlogic.handler.load_config")
    def test_configure_valid(self, load_config, set_logger, set_config):
        logger = MagicMock()
        config = MagicMock()
        load_config.return_value = config
        configure(logger, "dir")
        load_config.assert_called_once_with(logger, "dir")
        set_logger.assert_called_once_with(logger)
        set_config.assert_called_once_with(config)


@patch("hcoopmeetbotlogic.handler.logger")
class TestHandlers:
    @patch("hcoopmeetbotlogic.handler.dispatch")
    @patch("hcoopmeetbotlogic.handler.is_startmeeting")
    @patch("hcoopmeetbotlogic.handler.add_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_irc_message_no_meeting(self, get_meeting, add_meeting, is_startmeeting, dispatch, logger, context):
        message = MagicMock(nick="nick", channel="channel", network="network")
        get_meeting.return_value = None
        is_startmeeting.return_value = False
        irc_message(context, message)
        is_startmeeting.assert_called_once_with(message)
        add_meeting.assert_not_called()
        dispatch.assert_not_called()

    @patch("hcoopmeetbotlogic.handler.dispatch")
    @patch("hcoopmeetbotlogic.handler.is_startmeeting")
    @patch("hcoopmeetbotlogic.handler.add_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_irc_message_with_meeting(self, get_meeting, add_meeting, is_startmeeting, dispatch, logger, context):
        message = MagicMock(nick="nick", channel="channel", network="network")
        meeting = MagicMock()
        meeting.track_message = MagicMock(return_value="xxx")
        get_meeting.return_value = meeting
        irc_message(context, message)
        is_startmeeting.assert_not_called()
        add_meeting.assert_not_called()
        meeting.track_message.assert_called_once_with(message)
        dispatch.assert_called_once_with(meeting, context, "xxx")

    @patch("hcoopmeetbotlogic.handler.dispatch")
    @patch("hcoopmeetbotlogic.handler.is_startmeeting")
    @patch("hcoopmeetbotlogic.handler.add_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_irc_message_start_meeting(self, get_meeting, add_meeting, is_startmeeting, dispatch, logger, context):
        message = MagicMock(nick="nick", channel="channel", network="network")
        meeting = MagicMock()
        meeting.track_message = MagicMock(return_value="xxx")
        get_meeting.return_value = None
        is_startmeeting.return_value = True
        add_meeting.return_value = meeting
        irc_message(context, message)
        is_startmeeting.assert_called_once_with(message)
        add_meeting.assert_called_once_with(nick="nick", channel="channel", network="network")
        meeting.track_message.assert_called_once_with(message)
        dispatch.assert_called_once_with(meeting, context, "xxx")

    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_outbound_message_no_meeting(self, get_meeting, logger, context):
        get_meeting.return_value = None
        message = MagicMock(channel="channel", network="network")
        outbound_message(context, message)
        get_meeting.assert_called_once_with("channel", "network")

    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_outbound_message_with_meeting(self, get_meeting, logger, context):
        meeting = MagicMock()
        meeting.track_message = MagicMock()
        get_meeting.return_value = meeting
        message = MagicMock(channel="channel", network="network")
        outbound_message(context, message)  # just make sure it doesn't blow up
        get_meeting.assert_called_once_with("channel", "network")
        meeting.track_message.assert_called_once_with(message)


@patch("hcoopmeetbotlogic.handler.logger")
class TestCommands:
    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.DATE", "2001-02-03")
    @patch("hcoopmeetbotlogic.handler.VERSION", "1.2.3")
    def test_meetversion(self, send_reply, logger, context):
        meetversion(context)
        send_reply.assert_called_once_with(context, "HCoop Meetbot v1.2.3 (2001-02-03)")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_listmeetings_no_meetings(self, get_meetings, send_reply, logger, context):
        get_meetings.return_value = []
        listmeetings(context)
        get_meetings.assert_called_once_with(active=True, completed=False)
        send_reply.assert_called_once_with(context, "No active meetings")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_listmeetings_with_meetings(self, get_meetings, send_reply, logger, context):
        meeting1 = MagicMock()
        meeting1.display_name = MagicMock(return_value="xxx")
        meeting2 = MagicMock()
        meeting2.display_name = MagicMock(return_value="yyy")
        get_meetings.return_value = [meeting1, meeting2]
        listmeetings(context)
        get_meetings.assert_called_once_with(active=True, completed=False)
        send_reply.assert_called_once_with(context, "xxx, yyy")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_savemeetings_no_meetings(self, get_meetings, send_reply, logger, context):
        get_meetings.return_value = []
        savemeetings(context)
        get_meetings.assert_called_once_with(active=True, completed=False)
        send_reply.assert_called_once_with(context, "No meetings to save")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.config")
    @patch("hcoopmeetbotlogic.handler.write_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_savemeetings_with_meeting(self, get_meetings, write_meeting, config, send_reply, logger, context):
        meeting = MagicMock()
        config.return_value = "xxx"
        get_meetings.return_value = [meeting]
        savemeetings(context)
        get_meetings.assert_called_once_with(active=True, completed=False)
        write_meeting.assert_has_calls([call(config="xxx", meeting=meeting)])
        send_reply.assert_called_once_with(context, "Saved 1 meeting")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.config")
    @patch("hcoopmeetbotlogic.handler.write_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_savemeetings_with_meetings(self, get_meetings, write_meeting, config, send_reply, logger, context):
        meeting1 = MagicMock()
        meeting2 = MagicMock()
        config.return_value = "xxx"
        get_meetings.return_value = [meeting1, meeting2]
        savemeetings(context)
        get_meetings.assert_called_once_with(active=True, completed=False)
        write_meeting.assert_has_calls([call(config="xxx", meeting=meeting1), call(config="xxx", meeting=meeting2)])
        send_reply.assert_called_once_with(context, "Saved 2 meetings")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_addchair_not_found(self, get_meeting, send_reply, logger, context):
        get_meeting.return_value = None
        addchair(context, "channel", "network", "nick")
        get_meeting.assert_called_once_with("channel", "network")
        send_reply.assert_called_once_with(context, "Meeting not found for channel/network")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_addchair_found(self, get_meeting, send_reply, logger, context):
        meeting = MagicMock()
        meeting.chair = "yyy"
        meeting.add_chair = MagicMock()
        meeting.display_name = MagicMock(return_value="xxx")
        get_meeting.return_value = meeting
        addchair(context, "channel", "network", "nick")
        get_meeting.assert_called_once_with("channel", "network")
        meeting.add_chair.assert_called_once_with("nick", primary=True)
        send_reply.assert_called_once_with(context, "yyy is now the primary chair for xxx")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.write_meeting")
    @patch("hcoopmeetbotlogic.handler.deactivate_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_deletemeeting_not_found(self, get_meeting, deactivate_meeting, write_meeting, send_reply, logger, context):
        get_meeting.return_value = None
        deletemeeting(context, "channel", "network", True)
        get_meeting.assert_called_once_with("channel", "network")
        deactivate_meeting.assert_not_called()
        write_meeting.assert_not_called()
        send_reply.assert_called_once_with(context, "Meeting not found for channel/network")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.write_meeting")
    @patch("hcoopmeetbotlogic.handler.deactivate_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_deletemeeting_found_no_save(self, get_meeting, deactivate_meeting, write_meeting, send_reply, logger, context):
        meeting = MagicMock()
        meeting.display_name = MagicMock(return_value="xxx")
        get_meeting.return_value = meeting
        deletemeeting(context, "channel", "network", False)
        get_meeting.assert_called_once_with("channel", "network")
        deactivate_meeting.assert_called_once_with(meeting, retain=False)
        write_meeting.assert_not_called()
        send_reply.assert_called_once_with(context, "Meeting xxx has been deleted")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.config")
    @patch("hcoopmeetbotlogic.handler.write_meeting")
    @patch("hcoopmeetbotlogic.handler.deactivate_meeting")
    @patch("hcoopmeetbotlogic.handler.get_meeting")
    def test_deletemeeting_found_save(self, get_meeting, deactivate_meeting, write_meeting, config, send_reply, logger, context):
        meeting = MagicMock()
        meeting.display_name = MagicMock(return_value="xxx")
        config.return_value = "yyy"
        get_meeting.return_value = meeting
        deletemeeting(context, "channel", "network", True)
        get_meeting.assert_called_once_with("channel", "network")
        write_meeting.assert_called_once_with(config="yyy", meeting=meeting)
        deactivate_meeting.assert_called_once_with(meeting, retain=False)
        send_reply.assert_called_once_with(context, "Meeting xxx has been deleted (saved first)")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_recent_no_meetings(self, get_meetings, send_reply, logger, context):
        get_meetings.return_value = []
        recent(context)
        get_meetings.assert_called_once_with(active=False, completed=True)
        send_reply.assert_called_once_with(context, "No recent meetings")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.get_meetings")
    def test_recent_with_meetings(self, get_meetings, send_reply, logger, context):
        meeting1 = MagicMock()
        meeting1.display_name = MagicMock(return_value="meeting1")
        meeting2 = MagicMock()
        meeting2.display_name = MagicMock(return_value="meeting2")
        get_meetings.return_value = [meeting1, meeting2]
        recent(context)
        get_meetings.assert_called_once_with(active=False, completed=True)
        send_reply.assert_called_once_with(context, "meeting1, meeting2")

    @patch("hcoopmeetbotlogic.handler._send_reply")
    @patch("hcoopmeetbotlogic.handler.list_commands")
    def test_commands(self, list_commands, send_reply, logger, context):
        list_commands.return_value = ["a", "b", "c"]
        commands(context)
        send_reply.assert_has_calls(
            [
                call(context, "Available commands: a, b, c"),
                call(context, "See also: https://hcoop-meetbot.readthedocs.io/en/stable/"),
            ]
        )
