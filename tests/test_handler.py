# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=no-self-use,protected-access,redefined-outer-name

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hcoopmeetbotlogic.handler import (
    _config,
    _logger,
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

MISSING_DIR = "bogus"
VALID_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_handler/valid")
INVALID_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_handler/invalid")


@pytest.fixture
def context():
    context = MagicMock()
    context.send_reply = MagicMock()
    return context


class TestConfig:
    def test_configure_valid(self):
        """Test for valid configuration."""
        logger = MagicMock()
        conf_dir = VALID_DIR
        configure(logger, conf_dir)
        assert _logger() is logger
        assert _config().conf_file == os.path.join(VALID_DIR, "HcoopMeetbot.conf")
        assert _config().log_dir == "/tmp/meetings"
        assert _config().pattern == "%(channel)s-%%Y%%m%%d%%H%%M"
        assert _config().timezone == "America/Chicago"

    def test_configure_invalid(self):
        """Test for invalid configuration, which gets defaults."""
        logger = MagicMock()
        conf_dir = INVALID_DIR
        configure(logger, conf_dir)
        assert _logger() is logger
        assert _config().conf_file is None
        assert _config().log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert _config().pattern == "%%Y/%(channel)s.%%Y%%m%%d.%%H%%M"
        assert _config().timezone == "UTC"

    def test_configure_missing(self):
        """Test for missing configuration, which gets defaults."""
        logger = MagicMock()
        conf_dir = MISSING_DIR
        configure(logger, conf_dir)
        assert _logger() is logger
        assert _config().conf_file is None
        assert _config().log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert _config().pattern == "%%Y/%(channel)s.%%Y%%m%%d.%%H%%M"
        assert _config().timezone == "UTC"


class Handlers:
    def test_irc_message(self, context):
        """Test the irc_message handler."""
        message = MagicMock()
        irc_message(context, message)  # just make sure it doesn't blow up

    def test_outbound_message(self, context):
        """Test the outbound_message handler."""
        message = MagicMock()
        outbound_message(context, message)  # just make sure it doesn't blow up


class Commands:
    def test_meetversion(self, context):
        """Test the meetversion command."""
        meetversion(context)
        context.send_reply.assert_called_once()
        assert context.send_reply.call_args_list[0].starts_with("HcoopMeetbot v")

    def test_listmeetings(self, context):
        """Test the listmeetings command."""
        listmeetings(context)  # just make sure it doesn't blow up

    def test_savemeetings(self, context):
        """Test the listmeetings command."""
        savemeetings(context)  # just make sure it doesn't blow up

    def test_addchair(self, context):
        """Test the listmeetings command."""
        addchair(context, "channel", "network", "nick")  # just make sure it doesn't blow up

    def test_deletemeeting(self, context):
        """Test the listmeetings command."""
        deletemeeting(context, "channel", "network", True)  # just make sure it doesn't blow up

    def test_recent(self, context):
        """Test the listmeetings command."""
        recent(context)  # just make sure it doesn't blow up
