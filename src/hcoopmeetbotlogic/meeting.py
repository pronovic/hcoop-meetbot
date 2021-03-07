# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Meeting state.
"""

import uuid
from datetime import datetime
from typing import List, Optional

import attr
from pytz import timezone, utc

from .interface import Message


@attr.s(frozen=True)
class TrackedMessage:
    """
    A message tracked as part of a meeting.

    Attributes:
        sender(str): IRC nick of the sender
        payload(str): Payload of the message
        action(bool): Whether this is an ACTION message
        timestamp(datetime): Message timestamp in UTC
    """

    sender = attr.ib(type=str)
    payload = attr.ib(type=str)
    action = attr.ib(type=bool)
    timestamp = attr.ib(type=datetime)

    @timestamp.default
    def _default_start_time(self) -> datetime:
        return datetime.now(utc)


@attr.s
class Meeting:
    """
    A meeting on a particular IRC channel.

    Attributes:
        id(str): Unique identifier for the meeting
        founder(str): IRC nick of the meeting founder always a member of chairs
        channel(str): Channel the meeting is running on
        network(str): Network associated with the channel
        chair(str): IRC nick of primary meeting chair, always a member of chairs
        chairs(List[str]): IRC nick of all meeting chairs, including the primary
        start_time(datetime): Start time of the meeting in UTC
        end_time(Optional[datetime]): End time of the meeting in UTC, possibly None
        messages(List[TrackedMessage]): List of all messages tracked as part of the meeting
    """

    founder = attr.ib(type=str)
    channel = attr.ib(type=str)
    network = attr.ib(type=str)
    id = attr.ib(type=str)
    chair = attr.ib(type=str)
    chairs = attr.ib(type=List[str])
    start_time = attr.ib(type=datetime)
    end_time = attr.ib(type=Optional[datetime])
    messages = attr.ib(type=List[TrackedMessage])

    @id.default
    def _default_id(self) -> str:
        return uuid.uuid4().hex

    @chair.default
    def _default_chair(self) -> str:
        return self.founder

    @chairs.default
    def _default_chairs(self) -> List[str]:
        return [self.chair]

    @start_time.default
    def _default_start_time(self) -> datetime:
        return datetime.now(utc)

    @end_time.default
    def _default_end_time(self) -> Optional[datetime]:
        return None

    @messages.default
    def _default_messages(self) -> List[TrackedMessage]:
        return []

    @staticmethod
    def meeting_key(channel: str, network: str) -> str:
        """Build the dict key for a network and channel."""
        return "%s/%s" % (channel, network)

    def key(self) -> str:
        return Meeting.meeting_key(self.channel, self.network)

    def mark_completed(self) -> None:
        """Mark the meeting as completed."""
        self.end_time = datetime.now(utc)

    def add_chair(self, nick: str, primary: bool = True) -> None:
        """Add a chair to a meeting, potentially making it the primary chair."""
        if not nick in self.chairs:
            self.chairs.append(nick)
            self.chairs.sort()
        if primary:
            self.chair = nick

    def track_message(self, message: Message) -> TrackedMessage:
        """Track a message associated with the meeting."""
        # Per Wikipedia, actions start and end with \x01 (CTRL-A).
        # See "DCC CHAT" under: https://en.wikipedia.org/wiki/Client-to-client_protocol
        # To generate an action in an IRC client like irssi, use /action.
        payload = message.payload.strip(" \x01")
        action = payload[:6] == "ACTION"
        payload = payload[7:].strip() if action else payload.strip()
        tracked = TrackedMessage(action=action, sender=message.nick, payload=payload)
        self.messages.append(tracked)
        return tracked

    def active(self) -> bool:
        """Whether the meeting is active."""
        return self.end_time is None

    def display_name(self, zone: str = "UTC", fmt: str = "%Y-%m-%dT%H:%M%z") -> str:
        """Get the meeting display name."""
        return "%s/%s@%s" % (self.channel, self.network, self.start_time.astimezone(timezone(zone)).strftime(fmt))
