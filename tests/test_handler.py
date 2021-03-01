# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument,redefined-outer-name:

from unittest.mock import MagicMock, patch

import pytest

from hcoopmeetbotlogic.handler import (
    addchair,
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


class TestConfig:
    @patch("hcoopmeetbotlogic.handler.set_config")
    @patch("hcoopmeetbotlogic.handler.set_logger")
    @patch("hcoopmeetbotlogic.handler.load_config")
    def test_configure(self, load_config, set_logger, set_config):
        """Test for valid configuration."""
        logger = MagicMock()
        config = MagicMock()
        load_config.return_value = config
        configure(logger, "dir")
        load_config.assert_called_once_with(logger, "dir")
        set_logger.assert_called_once_with(logger)
        set_config.assert_called_once_with(config)


@patch("hcoopmeetbotlogic.handler.logger")
class TestHandlers:
    def test_irc_message(self, logger, context):
        """Test the irc_message handler."""
        message = MagicMock()
        irc_message(context, message)  # just make sure it doesn't blow up

    def test_outbound_message(self, logger, context):
        """Test the outbound_message handler."""
        message = MagicMock()
        outbound_message(context, message)  # just make sure it doesn't blow up


@patch("hcoopmeetbotlogic.handler.logger")
class TestCommands:
    def test_meetversion(self, logger, context):
        """Test the meetversion command."""
        meetversion(context)
        context.send_reply.assert_called_once()
        assert context.send_reply.call_args_list[0].starts_with("HcoopMeetbot v")

    def test_listmeetings(self, logger, context):
        """Test the listmeetings command."""
        listmeetings(context)  # just make sure it doesn't blow up

    def test_savemeetings(self, logger, context):
        """Test the listmeetings command."""
        savemeetings(context)  # just make sure it doesn't blow up

    def test_addchair(self, logger, context):
        """Test the listmeetings command."""
        addchair(context, "channel", "network", "nick")  # just make sure it doesn't blow up

    def test_deletemeeting(self, logger, context):
        """Test the listmeetings command."""
        deletemeeting(context, "channel", "network", True)  # just make sure it doesn't blow up

    def test_recent(self, logger, context):
        """Test the listmeetings command."""
        recent(context)  # just make sure it doesn't blow up
