# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
IRC request and message handlers.
"""

from logging import Logger

from .config import load_config
from .interface import Context, Message
from .release import DATE, VERSION
from .state import config, get_meeting, get_meetings, logger, move_to_complete, set_config, set_logger


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
    logger().debug("Received message: %s", message)
    meeting = get_meeting(message.channel, message.network)
    if meeting:
        meeting.track_message(message, dispatch=True)  # commands within inbound messages are dispatched


def outbound_message(context: Context, message: Message) -> None:  # pylint: disable=unused-argument:
    """
    Handle an outbound message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    logger().debug("Received message: %s", message)
    meeting = get_meeting(message.channel, message.network)
    if meeting:
        meeting.track_message(message, dispatch=False)  # commands within outbound messages are ignored


def meetversion(context: Context) -> None:  # pylint: disable=unused-argument:
    """Reply with a string describing the version of the plugin."""
    _send_reply(context, "HcoopMeetbot v%s, released %s" % (VERSION, DATE))


def listmeetings(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    List all currently-active meetings.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled listmeetings")
    meetings = get_meetings(active=True, completed=False)
    _send_reply(context, "No active meetings" if not meetings else ", ".join([m.display_name() for m in meetings]))


def savemeetings(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    Save all currently active meetings.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled savemeetings")
    meetings = get_meetings(active=True, completed=False)
    if not meetings:
        reply = "No meetings to save"
    else:
        for meeting in meetings:
            meeting.save(config=config())
        reply = "Saved %d meetings" % len(meetings)
    _send_reply(context, reply)


def addchair(context: Context, channel: str, network: str, nick: str) -> None:  # pylint: disable=unused-argument:
    """
    Add a nickname as a chair to the meeting.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to add the chair for
        network(str): Network to add the chair for
        nick(str): Nickname to add as the chair
    """
    logger().debug("Handled addchair for %s/%s nick=%s", channel, network, nick)
    meeting = get_meeting(channel, network)
    if not meeting:
        reply = "Meeting not found for %s/%s" % (channel, network)
    else:
        meeting.add_chair(nick, primary=True)
        reply = "%s is now the primary chair for %s" % (meeting.chair, meeting.display_name())
    _send_reply(context, reply)


def deletemeeting(context: Context, channel: str, network: str, save: bool) -> None:  # pylint: disable=unused-argument:
    """
    Delete a meeting from the cache.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to delete the meeting for
        network(str): Network to delete the meeting for
        save(bool): Whether to save the meeting before deleting it
    """
    logger().debug("Handled deletemeeting for %s/%s save=%s", channel, network, save)
    meeting = get_meeting(channel, network)
    if not meeting:
        reply = "Meeting not found for %s/%s" % (channel, network)
    else:
        meeting.mark_completed()
        move_to_complete(meeting)
        if save:
            meeting.save(config=config())
        reply = "Meeting %s has been deleted%s" % (meeting.display_name(), " (saved first)" if save else "")
    _send_reply(context, reply)


def recent(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    List recent meetings for admin purposes.

    Args:
        context(Context): Context for a message or command
    """
    logger().debug("Handled recent")
    meetings = get_meetings(active=False, completed=True)
    reply = "No recent meetings" if not meetings else ", ".join([m.display_name() for m in meetings])
    _send_reply(context, reply)
