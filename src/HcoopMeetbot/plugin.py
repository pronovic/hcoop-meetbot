# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=ungrouped-imports:

"""
Implement the HcoopMeetbot plugin in terms of Limnoria functionality.
"""

# This code is intentionally very thin.  All of the real functionality lives in the local package.
# All this code does is set up the right data to invoke the backend functionality.  This is done
# mainly for legibility, since it keeps the plugin-specific processing code separate from the
# business logic.  However, it also simplifies MyPy type checking.  Limnoria has no type hints,
# so by restricting its use to this module, the rest of the code can be more easily type checked.

import supybot.ircmsgs as ircmsgs
from supybot import callbacks
from supybot.commands import optional, wrap

from HcoopMeetbot.local.handler import (
    handle_addchair,
    handle_deletemeeting,
    handle_listmeetings,
    handle_message,
    handle_recent,
    handle_savemeetings,
)
from HcoopMeetbot.local.interface import Context, Message


def _context(plugin, irc, msg) -> Context:
    """Create context for a command or message."""
    channel = msg.args[0]
    return Context(
        logger=plugin.log,
        set_topic=lambda topic: irc.sendMsg(ircmsgs.topic(channel, topic)),
        send_reply=irc.reply if hasattr(irc, "reply") and callable(irc.reply) else lambda x: None,
        send_message=lambda message: irc.sendMsg(ircmsgs.privmsg(channel, message)),
    )


# pylint: disable=too-many-ancestors,invalid-name:
class HcoopMeetbot(callbacks.Plugin):
    """Helps run IRC meetings."""

    def doPrivmsg(self, irc, msg):
        """Capture all messages from supybot."""
        context = _context(self, irc, msg)
        message = Message(
            nick=msg.nick,
            channel=msg.args[0],
            network=irc.msg.tags["receivedOn"],
            payload=msg.args[1],
            topic=irc.state.channels[msg.args[0]].topic,
            channel_nicks=irc.state.channels[msg.args[0]].users,
        )
        handle_message(context=context, message=message)

    def outFilter(self, irc, msg):
        """Log outgoing messages from supybot."""
        try:
            if msg.command in ("PRIVMSG",):
                context = _context(self, irc, msg)
                message = Message(nick=irc.nick, channel=msg.args[0], network=irc.network, payload=msg.args[1])
                handle_message(context=context, message=message, bypass=True)
        except Exception:  # pylint: disable=broad-except:
            # Per original MeetBot, catch errors to prevent all output from being clobbered
            self.log.exception("Discarded error in outFilter")
        return msg

    def listmeetings(self, irc, msg, args):  # pylint: disable=unused-argument:
        """List all currently-active meetings."""
        context = _context(self, irc, msg)
        handle_listmeetings(context=context)

    listmeetings = wrap(listmeetings, ["admin"])

    def savemeetings(self, irc, msg, args):  # pylint: disable=unused-argument:
        """Save all currently active meetings"""
        context = _context(self, irc, msg)
        handle_savemeetings(context=context)

    savemeetings = wrap(savemeetings, ["admin"])

    def addchair(self, irc, msg, args, channel, network, nick):  # pylint: disable=unused-argument:
        """Add a nickname as a chair to the meeting: addchair <channel> <nick>."""
        context = _context(self, irc, msg)
        handle_addchair(context=context, channel=channel, network=network, nick=nick)

    addchair = wrap(addchair, ["admin", "channel", "something", "nick"])

    def deletemeeting(self, irc, msg, args, channel, network, save):  # pylint: disable=unused-argument:
        """Delete a meeting from the cache: deletemeeting <meeting> <save=true/false>"""
        context = _context(self, irc, msg)
        handle_deletemeeting(context=context, channel=channel, network=network, save=save)

    deletemeeting = wrap(deletemeeting, ["admin", "channel", "something", optional("boolean", True)])

    def recent(self, irc, msg, args):  # pylint: disable=unused-argument:
        """List recent meetings for admin purposes."""
        context = _context(self, irc, msg)
        handle_recent(context=context)

    recent = wrap(recent, ["admin"])


Class = HcoopMeetbot
