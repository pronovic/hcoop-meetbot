# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
IRC request and message handlers.
"""

from logging import Logger

from .command import dispatch, is_startmeeting, list_commands
from .config import load_config
from .interface import Context, Message
from .release import DATE, DOCS, VERSION
from .state import add_meeting, config, deactivate_meeting, get_meeting, get_meetings, logger, set_config, set_logger
from .writer import write_meeting


def _send_reply(context: Context, reply: str) -> None:
    """Send a reply to a context, logging it at DEBUG level first."""
    logger().debug(reply)
    context.send_reply(reply)


# noinspection PyShadowingNames
def configure(logger: Logger, conf_dir: str) -> None:  # pylint: disable=redefined-outer-name:
    """
    Configure the plugin.

    Args:
        logger(Logger): Python logger instance that should be used during processing
        conf_dir(str): Limnoria bot conf directory to load configuration from
    """
    logger.debug("Configuring plugin")
    config = load_config(logger, conf_dir)  # pylint: disable=redefined-outer-name:
    set_logger(logger)
    set_config(config)


def irc_message(context: Context, message: Message) -> None:  # pylint: disable=unused-argument:
    """
    Handle an IRC message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    logger().debug("Handled IRC message: %s", message)
    meeting = get_meeting(message.channel, message.network)
    if meeting:
        tracked = meeting.track_message(message)
        dispatch(meeting, context, tracked)
    elif is_startmeeting(message):
        meeting = add_meeting(nick=message.nick, channel=message.channel, network=message.network)
        tracked = meeting.track_message(message)
        dispatch(meeting, context, tracked)


def outbound_message(context: Context, message: Message) -> None:  # pylint: disable=unused-argument:
    """
    Handle an outbound message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    logger().debug("Handled outbound message: %s", message)
    meeting = get_meeting(message.channel, message.network)
    if meeting:
        # note that outbound messages are never dispatched, even if they contain a command
        meeting.track_message(message)


def meetversion(context: Context) -> None:  # pylint: disable=unused-argument:
    """Reply with a string describing the version of the plugin."""
    logger().debug("Handled 'meetversion'")
    _send_reply(context, "HCoop Meetbot v%s (%s)" % (VERSION, DATE))


def listmeetings(context: Context) -> None:
    """
    List all currently-active meetings.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled 'listmeetings'")
    meetings = get_meetings(active=True, completed=False)
    _send_reply(context, "No active meetings" if not meetings else ", ".join([m.display_name() for m in meetings]))


def savemeetings(context: Context) -> None:
    """
    Save all currently active meetings.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled 'savemeetings'")
    meetings = get_meetings(active=True, completed=False)
    if not meetings:
        reply = "No meetings to save"
    else:
        for meeting in meetings:
            write_meeting(config=config(), meeting=meeting)
        reply = "Saved %d meeting%s" % (len(meetings), "s" if len(meetings) > 1 else "")
    _send_reply(context, reply)


def addchair(context: Context, channel: str, network: str, nick: str) -> None:
    """
    Add a nickname as a chair to the meeting.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to add the chair for
        network(str): Network to add the chair for
        nick(str): Nickname to add as the chair
    """
    logger().debug("Handled 'addchair' for %s/%s nick=%s", channel, network, nick)
    meeting = get_meeting(channel, network)
    if not meeting:
        reply = "Meeting not found for %s/%s" % (channel, network)
    else:
        meeting.add_chair(nick, primary=True)
        reply = "%s is now the primary chair for %s" % (meeting.chair, meeting.display_name())
    _send_reply(context, reply)


def deletemeeting(context: Context, channel: str, network: str, save: bool) -> None:
    """
    Delete a meeting, moving it out of active state without actually completing it.

    The meeting will not be maintained in the list of recent meetings, since it
    isn't technically completed.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to delete the meeting for
        network(str): Network to delete the meeting for
        save(bool): Whether to save the meeting before deactivating it
    """
    logger().debug("Handled 'deletemeeting' for %s/%s save=%s", channel, network, save)
    meeting = get_meeting(channel, network)
    if not meeting:
        reply = "Meeting not found for %s/%s" % (channel, network)
    else:
        if save:
            write_meeting(config=config(), meeting=meeting)
        deactivate_meeting(meeting, retain=False)
        reply = "Meeting %s has been deleted%s" % (meeting.display_name(), " (saved first)" if save else "")
    _send_reply(context, reply)


def recent(context: Context) -> None:
    """
    List recent meetings for admin purposes.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled 'recent'")
    meetings = get_meetings(active=False, completed=True)
    reply = "No recent meetings" if not meetings else ", ".join([m.display_name() for m in meetings])
    _send_reply(context, reply)


def commands(context: Context) -> None:
    """
    List available commands.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled 'commands'")
    _send_reply(context, "Available commands: %s" % ", ".join(list_commands()))
    _send_reply(context, "See also: %s" % DOCS)
