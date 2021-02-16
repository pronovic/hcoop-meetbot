# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
IRC request and message handlers.
"""

from .interface import Context, Message


def irc_message(context: Context, message: Message) -> None:
    """
    Handle an IRC message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    context.logger.info("Received message: %s", message)


def outbound_message(context: Context, message: Message) -> None:
    """
    Handle an outbound message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    context.logger.info("Received message: %s", message)


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
