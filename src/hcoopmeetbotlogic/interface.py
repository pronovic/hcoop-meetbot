# vim: set ft=python ts=4 sw=4 expandtab:

"""
Object interface used by plugin to access code in the local package.
"""

from collections.abc import Callable, Iterable
from datetime import datetime

from attrs import frozen


@frozen
class Context:
    # noinspection PyUnresolvedReferences
    """
    Context for a message or command, including callbacks that can be invoked.

    Attributes:
        get_topic(Callable[[], str]): Get the topic for the current context
        set_topic(Callable[[str], None]): Set a topic in the correct context
        send_reply(Callable[[str], None]): Send a reply in the current context
        send_message(Callable[[str], None]): Send a message to the server immediately
    """

    get_topic: Callable[[], str]
    set_topic: Callable[[str], None]
    send_reply: Callable[[str], None]
    send_message: Callable[[str], None]


@frozen
class Message:
    # noinspection PyUnresolvedReferences
    """
    A message to be processed.

    Attributes:
        id(str): Identifier for the message
        timestamp(str): Time the message was received
        nick(str): Nickname of the IRC user that sent the message
        channel(str): Channel the message was sent to
        network(str): Network the message was sent on
        payload(str): Message payload
        topic(Optional[str]): Current topic of the channel
        channel_nicks(Optional[Iterable[str]]): List of nicknames currently in the channel
    """

    id: str
    timestamp: datetime
    nick: str
    channel: str
    network: str
    payload: str
    topic: str | None = None
    channel_nicks: Iterable[str] | None = None
