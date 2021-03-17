# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

# Note: this must be executed by supybot-test.  Use 'run test' from the command line.
#
# Unfortunately, tests must live alongside the source code for supybot-test to execute them.
# So, this lives here rather than in the tests modules with all of the other unit tests.
from datetime import datetime
from unittest.mock import ANY, MagicMock, call, patch

from supybot.test import ChannelPluginTestCase

from HcoopMeetbot.plugin import _context
from hcoopmeetbotlogic.interface import Message

# These are values used by the plugin test case
ID = "id"
NICK = "test"
CHANNEL = "#test"
NETWORK = "test"
PREFIX = "@"
TIMESTAMP = datetime(2021, 3, 7, 13, 14, 0)


def _stub(context, **kwargs):  # pylint: disable=unused-argument:
    """Stub handler method that returns a static reply; without this, the handler tests all time out."""
    context.send_reply("Hello")


def _inbound(payload: str):
    """Generate an expected inbound message generated via doPrivmsg()."""
    return Message(
        id=ID,
        timestamp=TIMESTAMP,
        nick=NICK,
        channel=CHANNEL,
        network=NETWORK,
        payload="%s%s" % (PREFIX, payload),
        topic="",
        channel_nicks=[NICK],
    )


def _outbound():
    """Generate an expected outbound message returned to the caller based on the _stub() call"""
    return Message(id=ID, timestamp=TIMESTAMP, nick=NICK, channel=CHANNEL, network=NETWORK, payload="%s: Hello" % NICK)


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

        channel = MagicMock(topic="topic")
        channels = {"channel": channel}
        state = MagicMock(channels=channels)

        irc = MagicMock(state=state)
        irc.sendMsg = MagicMock()
        irc.reply = MagicMock()

        result = _context(plugin, irc, msg)
        assert result.get_topic() == "topic"

        result.set_topic("provided-topic")
        result.send_reply("provided-reply")
        result.send_message("provided-message")

        topic.assert_called_once_with("channel", "provided-topic")
        privmsg.assert_called_once_with("channel", "provided-message")
        irc.sendMsg.assert_has_calls([call("generated-topic"), call("generated-message")])

    @patch("HcoopMeetbot.plugin.handler.meetversion")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_meetversion(self, uuid4, now, irc_message, outbound_message, meetversion) -> None:
        """Test the meetversion command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        meetversion.side_effect = _stub
        self.assertNotError("meetversion")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("meetversion"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        meetversion.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.listmeetings")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_listmeetings(self, uuid4, now, irc_message, outbound_message, listmeetings) -> None:
        """Test the listmeetings command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        listmeetings.side_effect = _stub
        self.assertNotError("listmeetings")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("listmeetings"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        listmeetings.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.savemeetings")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_savemeetings(self, uuid4, now, irc_message, outbound_message, savemeetings) -> None:
        """Test the savemeetings command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        savemeetings.side_effect = _stub
        self.assertNotError("savemeetings")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("savemeetings"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        savemeetings.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.addchair")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_addchair(self, uuid4, now, irc_message, outbound_message, addchair) -> None:
        """Test the addchair command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        addchair.side_effect = _stub
        self.assertNotError("addchair nick")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("addchair nick"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        addchair.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, nick="nick")

    @patch("HcoopMeetbot.plugin.handler.deletemeeting")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_deletemeeting_save(self, uuid4, now, irc_message, outbound_message, deletemeeting) -> None:
        """Test the deletemeeting command,.save=True"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        deletemeeting.side_effect = _stub
        self.assertNotError("deletemeeting true")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("deletemeeting true"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        deletemeeting.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, save=True)

    @patch("HcoopMeetbot.plugin.handler.deletemeeting")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_deletemeeting_nosave(self, uuid4, now, irc_message, outbound_message, deletemeeting) -> None:
        """Test the deletemeeting command,.save=False"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        deletemeeting.side_effect = _stub
        self.assertNotError("deletemeeting false")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("deletemeeting false"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        deletemeeting.assert_called_once_with(context=ANY, channel=CHANNEL, network=NETWORK, save=False)

    @patch("HcoopMeetbot.plugin.handler.recent")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_recent(self, uuid4, now, irc_message, outbound_message, recent) -> None:
        """Test the recent command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        recent.side_effect = _stub
        self.assertNotError("recent")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("recent"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        recent.assert_called_once_with(context=ANY)

    @patch("HcoopMeetbot.plugin.handler.commands")
    @patch("HcoopMeetbot.plugin.handler.outbound_message")
    @patch("HcoopMeetbot.plugin.handler.irc_message")
    @patch("HcoopMeetbot.plugin.now")
    @patch("HcoopMeetbot.plugin.uuid4")
    def test_commands(self, uuid4, now, irc_message, outbound_message, commands) -> None:
        """Test the commands command"""
        uuid4.return_value = MagicMock(hex=ID)
        now.return_value = TIMESTAMP
        commands.side_effect = _stub
        self.assertNotError("commands")
        irc_message.assert_called_once_with(context=ANY, message=_inbound("commands"))
        outbound_message.assert_called_once_with(context=ANY, message=_outbound())
        commands.assert_called_once_with(context=ANY)
