# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
IRC request and message handlers.
"""

from .interface import Context, Message


def ircmessage(context: Context, message: Message, bypass: bool = False) -> None:
    """
    Handle a message from the supybot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
        bypass(bool): Whether to bypass message processing
    """
    context.logger.info("Received message%s: %s", " (bypassed)" if bypass else "", message)


def listmeetings(context: Context) -> None:
    """
    List all currently-active meetings.

    Args:
        context(Context): Context for a message or command
    """
    context.logger.info("Handled listmeetings")


def savemeetings(context: Context) -> None:
    """
    Save all currently active meetings.

    Args:
        context(Context): Context for a message or command
    """
    context.logger.info("Handled savemeetings")


def addchair(context: Context, channel: str, network: str, nick: str) -> None:
    """
    Add a nickname as a chair to the meeting.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to add the chair for
        network(str): Network to add the chair for
        nick(str): Nickname to add as the chair
    """
    context.logger.info("Handled addchair for [%s] [%s] [%s]", channel, network, nick)


def deletemeeting(context: Context, channel: str, network: str, save: bool) -> None:
    """
    Delete a meeting from the cache.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to delete the meeting for
        network(str): Network to delete the meeting for
        save(bool): Whether to save the meeting before deleting it
    """
    context.logger.info("Handled deletemeeting for [%s] [%s] [%s]", channel, network, save)


def recent(context: Context) -> None:
    """
    List recent meetings for admin purposes."

    Args:
        context(Context): Context for a message or command
    """
    context.logger.info("Handled recent")
