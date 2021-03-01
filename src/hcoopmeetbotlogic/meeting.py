# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Meeting state.
"""

import uuid
from datetime import datetime, tzinfo
from enum import Enum
from typing import List, Optional

import attr
from pytz import utc

from .config import Config
from .interface import Message


class TrackedMessageType(Enum):
    """Types of tracked messages."""

    ACTION = "action"
    MESSAGE = "message"


# noinspection PyUnresolvedReferences
@attr.s
class TrackedMessage:
    """
    A message tracked as part of a meeting.

    Attributes:
        timestamp(datetime): Message timestamp in UTC
        sender(str): IRC nick of the sender
        payload(str): Payload of the message
        type(TrackedMessageType): Type of the message
    """

    sender = attr.ib(type=str)
    payload = attr.ib(type=str)
    type = attr.ib(type=TrackedMessageType)
    timestamp = attr.ib(type=datetime)

    @timestamp.default
    def _default_start_time(self) -> datetime:
        return datetime.now(utc)


class MeetingState(Enum):
    """Meeting state"""

    RUNNING = "running"
    COMPLETED = "completed"


# noinspection PyUnresolvedReferences
@attr.s
class Meeting:
    """
    A meeting on a particular IRC channel.

    Attributes:
        id(str): Unique identifier for the meeting
        channel(str): Channel the meeting is running on
        network(str): Network associated with the channel
        chairs(str): IRC nick of primary meeting chair, always a member of chairs
        chairs(List[str]): IRC nick of all meeting chairs, including the primary
        start_time(datetime): Start time of the meeting in UTC
        end_time(Optional[datetime]): End time of the meeting in UTC, possibly None
        messages(List[TrackedMessage]): List of all messages tracked as part of the meeting
    """

    channel = attr.ib(type=str)
    network = attr.ib(type=str)
    chair = attr.ib(type=str)
    chairs = attr.ib(type=List[str])
    id = attr.ib(type=str)
    state = attr.ib(type=MeetingState, default=MeetingState.RUNNING)
    start_time = attr.ib(type=datetime)
    end_time = attr.ib(type=Optional[datetime], default=None)
    messages = attr.ib(type=List[TrackedMessage])

    @id.default
    def _default_id(self) -> str:
        return uuid.uuid4().hex

    @chairs.default
    def _default_chairs(self) -> List[str]:
        return [self.chair]

    @start_time.default
    def _default_start_time(self) -> datetime:
        return datetime.now(utc)

    @messages.default
    def _default_messages(self) -> List[TrackedMessage]:
        return []

    @staticmethod
    def meeting_key(channel: str, network: str) -> str:
        """Build the dict key for a network and channel."""
        return "[%s]-[%s]" % (channel, network)

    def key(self) -> str:
        return Meeting.meeting_key(self.channel, self.network)

    def mark_completed(self) -> None:
        """Mark the meeting as completed."""
        self.state = MeetingState.COMPLETED
        self.end_time = datetime.now(utc)

    def add_chair(self, nick: str, primary: bool = True) -> None:
        """Add a chair to a meeting, potentially making it the primary chair."""
        if not nick in self.chairs:
            self.chairs.append(nick)
            self.chairs.sort()
        if primary:
            self.chair = nick

    def track_message(self, message: Message, dispatch: bool = False) -> None:
        """Track a message, optionally dispatching any embedded commands."""
        payload = message.payload.strip(" \x01")  # \x01 is present in actions
        message_type = TrackedMessageType.ACTION if payload[:6] == "ACTION" else TrackedMessageType.MESSAGE
        tracked = TrackedMessage(type=message_type, sender=message.nick, payload=payload)
        self.messages.append(tracked)
        if dispatch:
            pass  # TODO: figure out how to dispatch a message - handle whatever needs to be done

    def display_name(self, zone: tzinfo = utc, fmt: str = "%Y-%m-%dT%H:%M%z") -> str:
        """Get the message display name."""
        return "%s/%s@%s" % (self.channel, self.network, self.start_time.astimezone(zone).strftime(fmt))

    def save(self, config: Config) -> None:
        """Persist a meeting to disk per configuration."""
        # TODO: figure out how to persist a meeting to disk - handle whatever needs to be done
