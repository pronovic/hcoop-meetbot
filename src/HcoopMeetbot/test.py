# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

# Note: this must be executed by supybot-test.  Use 'run test' from the command line.
#
# Unfortunately, tests must live alongside the source code for supybot-test to execute them.
# So, this lives here rather than in the tests modules with all of the other unit tests.

from unittest.mock import ANY, MagicMock, call, patch

from supybot.test import ChannelPluginTestCase

from HcoopMeetbot.plugin import _context
from hcoopmeetbotlogic.interface import Message

# These are values used by the plugin test case
NICK = "test"
CHANNEL = "#test"
NETWORK = "test"
PREFIX = "@"


def _stub(context, **kwargs):  # pylint: disable=unused-argument:
    """Stub handler method that returns a static reply; without this, the handler tests all time out."""
    context.send_reply("Hello")


def _inbound(payload: str):
    """Generate an expected inbound message generated via doPrivmsg()."""
    return Message(nick=NICK, channel=CHANNEL, network=NETWORK, payload="%s%s" % (PREFIX, payload), topic="", channel_nicks=[NICK])


def _outbound():
    """Generate an expected outbound message returned to the caller based on the _stub() call"""
    return Message(nick=NICK, channel=CHANNEL, network=NETWORK, payload="%s: Hello" % NICK)


class HcoopMeetbotTestCase(ChannelPluginTestCase):  # type: ignore
    plugins = ("HcoopMeetbot",)

    @patch("HcoopMeetbot.plugin.ircmsgs.topic")
    @patch("HcoopMeetbot.plugin.ircmsgs.privmsg")
    def test_context(self, privmsg, topic):
        """Test behavior of the Context object returned by the _context() function."""
        topic.return_value = "generated-topic"
        privmsg.return_value = "generated-message"

        plugin = MagicMock()
        plugin.log = MagicMock()

        msg = MagicMock(args=["channel"])

        irc = MagicMock()
        irc.sendMsg = MagicMock()
        irc.reply = MagicMock()

        result = _context(plugin, irc, msg)
        result.set_topic("provided-topic")
        result.send_reply("provided-reply")
        result.send_message("provided-message")

        assert result.logger is plugin.log
        topic.assert_called_once_with("channel", "provided-topic")
        privmsg.assert_called_once_with("channel", "provided-message")
        irc.sendMsg.assert_has_calls([call("generated-topic"), call("generated-message")])

    @patch("HcoopMeetbot.plugin.handler.meetversion")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_meetversion(self, irc_message, outbound_message, meetversion) -> None:
        """Test the listmeetings command"""
        meetversion.side_effect = _stub
        self.assertNotError("meetversion")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("meetversion"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        meetversion.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.listmeetings")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_listmeetings(self, irc_message, outbound_message, listmeetings) -> None:
        """Test the listmeetings command"""
        listmeetings.side_effect = _stub
        self.assertNotError("listmeetings")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("listmeetings"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        listmeetings.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.savemeetings")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_savemeetings(self, irc_message, outbound_message, savemeetings) -> None:
        """Test the savemeetings command"""
        savemeetings.side_effect = _stub
        self.assertNotError("savemeetings")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("savemeetings"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        savemeetings.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.addchair")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_addchair(self, irc_message, outbound_message, addchair) -> None:
        """Test the addchair command"""
        addchair.side_effect = _stub
        self.assertNotError("addchair nick")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("addchair nick"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        addchair.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, nick="nick")

    @patch("HcoopMeetbot.plugin.handler.deletemeeting")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_deletemeeting_save(self, irc_message, outbound_message, deletemeeting) -> None:
        """Test the deletemeeting command,.save=True"""
        deletemeeting.side_effect = _stub
        self.assertNotError("deletemeeting true")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("deletemeeting true"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        deletemeeting.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, save=True)

    @patch("HcoopMeetbot.plugin.handler.deletemeeting")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_deletemeeting_nosave(self, irc_message, outbound_message, deletemeeting) -> None:
        """Test the deletemeeting command,.save=False"""
        deletemeeting.side_effect = _stub
        self.assertNotError("deletemeeting false")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("deletemeeting false"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        deletemeeting.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, save=False)

    @patch("HcoopMeetbot.plugin.handler.recent")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    def test_recent(self, irc_message, outbound_message, recent) -> None:
        """Test the recent command"""
        recent.side_effect = _stub
        self.assertNotError("recent")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("recent"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        recent.assert_called_once_with(context=ANY)
