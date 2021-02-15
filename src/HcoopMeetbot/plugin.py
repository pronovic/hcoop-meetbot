# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=too-many-ancestors,unused-argument,invalid-name,protected-access,unused-variable:

# This code was originally taken from the MeetBot package in MeetBot.  It
# was converted to Python 3, adjusted to address PyCharm and pylint warnings, and
# reformatted to match my coding standard with black and isort.  In a lot of
# cases, warnings have been ignored rather than introducing the risk of trying
# to fix them.

import time
import traceback
import importlib

import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs

from supybot.commands import wrap, optional

import HcoopMeetbot.local.meeting as meeting



meeting = importlib.reload(meeting)

# By doing this, we can not lose all of our meetings across plugin
# reloads.  But, of course, you can't change the source too
# drastically if you do that!
try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    meeting_cache
except NameError:
    meeting_cache = {}

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    recent_meetings
except NameError:
    recent_meetings = [ ]


class HcoopMeetbot(callbacks.Plugin):
    """-- help goes here --"""

    # Instead of using real supybot commands, I just listen to ALL
    # messages coming in and respond to those beginning with our
    # prefix char.  I found this helpful from a not duplicating logic
    # standpoint (as well as other things).  Ask me if you have more
    # questions.

    # This captures all messages coming into the bot.
    def doPrivmsg(self, irc, msg):
        nick = msg.nick
        channel = msg.args[0]
        payload = msg.args[1]
        network = irc.msg.tags['receivedOn']

        # The following is for debugging.  It's excellent to get an
        # interactive interperter inside of the live bot.  use
        # code.interact instead of my souped-up version if you aren't
        # on my computer:
        # if payload == 'interact':
        #    from rkddp.interact import interact ; interact()

        # Get our Meeting object, if one exists.  Have to keep track
        # of different servers/channels.
        # (channel, network) tuple is our lookup key.
        Mkey = (channel, network)
        M = meeting_cache.get(Mkey, None)

        # Start meeting if we are requested
        if payload[:13] == '#startmeeting':
            if M is not None:
                irc.error("Can't start another meeting, one is in progress.")
                return

            # This callback is used to send data to the channel:
            def _setTopic(x):
                irc.sendMsg(ircmsgs.topic(channel, x))

            def _sendReply(x):
                irc.sendMsg(ircmsgs.privmsg(channel, x))

            def _channelNicks():
                return irc.state.channels[channel].users

            M = meeting.Meeting(channel=channel, owner=nick,
                                oldtopic=irc.state.channels[channel].topic,
                                writeRawLog=True,
                                setTopic=_setTopic, sendReply=_sendReply,
                                getRegistryValue=self.registryValue,
                                safeMode=True, channelNicks=_channelNicks,
                                network=network,
                                )
            meeting_cache[Mkey] = M
            recent_meetings.append(
                (channel, network, time.ctime()))
            if len(recent_meetings) > 10:
                del recent_meetings[0]
        # If there is no meeting going on, then we quit
        if M is None: return
        # Add line to our meeting buffer.
        M.addline(nick, payload)
        # End meeting if requested:
        if M._meetingIsOver:
            # M.save()  # now do_endmeeting in M calls the save functions
            del meeting_cache[Mkey]

    def outFilter(self, irc, msg):
        """Log outgoing messages from supybot.
        """
        # Catch supybot's own outgoing messages to log them.  Run the
        # whole thing in a try: block to prevent all output from
        # getting clobbered.
        # noinspection PyBroadException
        try:
            if msg.command in ('PRIVMSG', ):
                # Note that we have to get our nick and network parameters
                # in a slightly different way here, compared to doPrivmsg.
                nick = irc.nick
                channel = msg.args[0]
                payload = msg.args[1]
                Mkey = (channel, irc.network)
                M = meeting_cache.get(Mkey, None)
                if M is not None:
                    M.addrawline(nick, payload)
        except: # pylint: disable=bare-except:
            print(traceback.print_exc())
            print("(above exception in outFilter, ignoring)")
        return msg

    # These are admin commands, for use by the bot owner when there
    # are many channels which may need to be independently managed.
    def listmeetings(self, irc, msg, args):
        """

        List all currently-active meetings."""
        reply = ""
        reply = ", ".join(str(x) for x in sorted(meeting_cache.keys()))
        if reply.strip() == '':
            irc.reply("No currently active meetings.")
        else:
            irc.reply(reply)

    listmeetings = wrap(listmeetings, ['admin'])

    # noinspection PyUnresolvedReferences
    def savemeetings(self, irc, msg, args):
        """

        Save all currently active meetings."""
        numSaved = 0
        for M in meeting_cache.items():
            M.config.save()
        irc.reply("Saved %d meetings." % numSaved)

    savemeetings = wrap(savemeetings, ['admin'])

    def addchair(self, irc, msg, args, channel, network, nick):
        """<channel> <network> <nick>

        Add a nick as a chair to the meeting."""
        Mkey = (channel, network)
        M = meeting_cache.get(Mkey, None)
        if not M:
            irc.reply("Meeting on channel %s, network %s not found" % (
                channel, network))
            return
        M.chairs.setdefault(nick, True)
        irc.reply("Chair added: %s on (%s, %s)." % (nick, channel, network))

    addchair = wrap(addchair, ['admin', "channel", "something", "nick"])

    def deletemeeting(self, irc, msg, args, channel, network, save):
        """<channel> <network> <saveit=True>

        Delete a meeting from the cache.  If save is given, save the
        meeting first, defaults to saving."""
        Mkey = (channel, network)
        if Mkey not in meeting_cache:
            irc.reply("Meeting on channel %s, network %s not found" % (
                channel, network))
            return
        if save:
            M = meeting_cache.get(Mkey, None)
            M.endtime = time.localtime()
            M.config.save()
        del meeting_cache[Mkey]
        irc.reply("Deleted: meeting on (%s, %s)." % (channel, network))

    deletemeeting = wrap(deletemeeting, ['admin', "channel", "something",
                                         optional("boolean", True)])

    def recent(self, irc, msg, args):
        """

        List recent meetings for admin purposes.
        """
        reply = []
        for channel, network, ctime in recent_meetings:
            Mkey = (channel, network)
            if Mkey in meeting_cache:
                state = ", running"
            else:
                state = ""
            reply.append("(%s, %s, %s%s)" % (channel, network, ctime, state))
        if reply:
            irc.reply(" ".join(reply))
        else:
            irc.reply("No recent meetings in internal state.")

    recent = wrap(recent, ['admin'])

    def pingall(self, irc, msg, args, message):
        """<text>

        Send a broadcast ping to all users on the channel.

        An message to be sent along with this ping must also be
        supplied for this command to work.
        """
        nick = msg.nick
        channel = msg.args[0]
        payload = msg.args[1]

        # We require a message to go out with the ping, we don't want
        # to waste people's time:
        if channel[0] != '#':
            irc.reply("Not joined to any channel.")
            return
        if message is None:
            irc.reply(
                "You must supply a description with the `pingall` command.")
            return

        # Send announcement message
        irc.sendMsg(ircmsgs.privmsg(channel, message))
        # ping all nicks in lines of about 256
        nickline = ''
        nicks = sorted(irc.state.channels[channel].users,
                       key=lambda x: x.lower())
        for nick in nicks:
            nickline = nickline + nick + ' '
            if len(nickline) > 256:
                irc.sendMsg(ircmsgs.privmsg(channel, nickline))
                nickline = ''
        irc.sendMsg(ircmsgs.privmsg(channel, nickline))
        # Send announcement message
        irc.sendMsg(ircmsgs.privmsg(channel, message))

    pingall = wrap(pingall, [optional('text', None)])

Class = HcoopMeetbot
