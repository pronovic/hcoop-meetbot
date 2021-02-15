# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Object interface used by plugin to access code in the local package.
"""
from logging import Logger
from typing import Callable, Iterable, Optional

import attr


@attr.s
class Context:
    """
    Context for a message or command, including callbacks that can be invoked.

    Attributes:
        logger(Logger): Python logger instance that should be used during processing
        set_topic(Callable[[str], None]): Set a topic in the correct context
        send_reply(Callable[[str], None]): Send a reply in the current context
        send_message(Callable[[str], None]): Send a message to the server immediately
    """

    logger = attr.ib(type=Logger)
    set_topic = attr.ib(type=Callable[[str], None])
    send_reply = attr.ib(type=Callable[[str], None])
    send_message = attr.ib(type=Callable[[str], None])


@attr.s
class Message:
    """
    A message to be processed.

    Attributes:
        nick(str): Nickname of the IRC user that sent the message
        channel(str): Channel the message was sent to
        network(str): Network the message was sent on
        payload(str): Message payload
        topic(Optional[str]): Current topic of the channel
        channel_nicks(Optional[Iterable[str]]): List of nicknames currently in the channel
    """

    nick = attr.ib(type=str)
    channel = attr.ib(type=str)
    network = attr.ib(type=str)
    payload = attr.ib(type=str)
    topic = attr.ib(type=Optional[str], default=None)
    channel_nicks = attr.ib(type=Optional[Iterable[str]], default=None)
