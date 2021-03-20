# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Meeting state.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import attr

from .dateutil import formatdate, now
from .interface import Message


class EventType(Enum):
    """Legal event types for TrackedEvent."""

    START_MEETING = "START_MEETING"
    END_MEETING = "END_MEETING"
    ATTENDEE = "ATTENDEE"
    MEETING_NAME = "MEETING_NAME"
    TOPIC = "TOPIC"
    ADD_CHAIR = "ADD_CHAIR"
    REMOVE_CHAIR = "REMOVE_CHAIR"
    TRACK_NICK = "TRACK_NICK"
    UNDO = "UNDO"
    SAVE_MEETING = "SAVE_MEETING"
    MOTION = "MOTION"
    VOTE = "VOTE"
    ACCEPTED = "ACCEPTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAILED = "FAILED"
    ACTION = "ACTION"
    INFO = "INFO"
    IDEA = "IDEA"
    HELP = "HELP"
    LINK = "LINK"


class VotingAction(Enum):
    """Voting actions"""

    IN_FAVOR = "+1"
    OPPOSED = "-1"


@attr.s(frozen=True)
class TrackedMessage:
    # noinspection PyUnresolvedReferences
    """
    A message tracked as part of a meeting.

    Attributes:
        id(str): Message identifier
        sender(str): IRC nick of the sender
        payload(str): Payload of the message
        action(bool): Whether this is an ACTION message
        timestamp(datetime): Message timestamp in UTC
    """

    id = attr.ib(type=str)
    sender = attr.ib(type=str)
    payload = attr.ib(type=str)
    action = attr.ib(type=bool)
    timestamp = attr.ib(type=datetime)

    def display_name(self) -> str:
        """Get the message display name."""
        return "%s@%s" % (self.id, formatdate(self.timestamp))


@attr.s(frozen=True)
class TrackedEvent:
    # noinspection PyUnresolvedReferences
    """
    An event tracked as part of a meeting, always tied to a specific message.

    Attributes:
        id(str): The event identifier
        event_type(EventType): Type of the event
        timestamp(datetime): Event timestamp in UTC
        message(TrackedMessage): The message associated with the event
        operand(Optional[str]): The operand (remainder of the payload after the command)
    """

    event_type = attr.ib(type=EventType)
    message = attr.ib(type=TrackedMessage)
    operand = attr.ib(type=Optional[Any])
    id = attr.ib(type=str)
    timestamp = attr.ib(type=datetime)

    @id.default
    def _default_id(self) -> str:
        return self.message.id

    @timestamp.default
    def _default_timestamp(self) -> datetime:
        return self.message.timestamp

    def display_name(self) -> str:
        """Get the event display name."""
        return "%s@%s" % (self.id, formatdate(self.timestamp))


# pylint: disable=too-many-instance-attributes:
@attr.s
class Meeting:
    # noinspection PyUnresolvedReferences
    """
    A meeting on a particular IRC channel.

    Attributes:
        id(str): Unique identifier for the meeting
        name(str): The name of the meeting, which defaults to the channel name
        founder(str): IRC nick of the meeting founder always a member of chairs
        channel(str): Channel the meeting is running on
        network(str): Network associated with the channel
        chair(str): IRC nick of primary meeting chair, always a member of chairs
        chairs(List[str]): IRC nick of all meeting chairs, including the primary
        nicks(List[str]): IRC nick of anyone who contributed to the meeting or was explicitly called out
        start_time(datetime): Start time of the meeting in UTC
        end_time(Optional[datetime]): End time of the meeting in UTC, possibly None
        original_topic(Optional[str]): The original topic assigned to the channel prior to starting the meeting
        current_topic(Optional[str]): The current topic, assigned by a chair
        messages(List[TrackedMessage]): List of all messages tracked as part of the meeting
        events(List[TrackedEvent]): List of all events tracked as part of the meeting
        aliases(Dict[str, Optional[str]): Dictionary mapping attendee IRC nick to optional alias
        vote_in_progress(bool): Whether voting is in progress
        motion_index(int): Index into events for the current motion, when voting is in progress
    """

    founder = attr.ib(type=str)
    channel = attr.ib(type=str)
    network = attr.ib(type=str)
    id = attr.ib(type=str)
    name = attr.ib(type=str)
    chair = attr.ib(type=str)
    chairs = attr.ib(type=List[str])
    nicks = attr.ib(type=Dict[str, int])
    start_time = attr.ib(type=datetime)
    end_time = attr.ib(type=Optional[datetime])
    active = attr.ib(type=bool, default=False)
    original_topic = attr.ib(type=Optional[str], default=None)
    current_topic = attr.ib(type=Optional[str], default=None)
    messages = attr.ib(type=List[TrackedMessage])
    events = attr.ib(type=List[TrackedEvent])
    aliases = attr.ib(type=Dict[str, Optional[str]])
    vote_in_progress = attr.ib(type=bool, default=False)
    motion_index = attr.ib(type=Optional[int], default=None)

    @id.default
    def _default_id(self) -> str:
        return uuid.uuid4().hex

    @chair.default
    def _default_chair(self) -> str:
        return self.founder

    @chairs.default
    def _default_chairs(self) -> List[str]:
        return [self.chair]

    @nicks.default
    def _default_nicks(self) -> Dict[str, int]:
        return {nick: 0 for nick in self.chairs}

    @start_time.default
    def _default_start_time(self) -> datetime:
        return now()

    @end_time.default
    def _default_end_time(self) -> Optional[datetime]:
        return None

    @messages.default
    def _default_messages(self) -> List[TrackedMessage]:
        return []

    @events.default
    def _default_events(self) -> List[TrackedEvent]:
        return []

    @aliases.default
    def _default_aliases(self) -> Dict[str, Optional[str]]:
        return {}

    @name.default
    def _default_meeting_name(self) -> str:
        return self.channel

    @staticmethod
    def meeting_key(channel: str, network: str) -> str:
        """Build the dict key for a network and channel."""
        return "%s/%s" % (channel, network)

    def key(self) -> str:
        return Meeting.meeting_key(self.channel, self.network)

    def display_name(self) -> str:
        """Get the meeting display name."""
        return "%s/%s@%s" % (self.channel, self.network, formatdate(self.start_time))

    def add_chair(self, nick: str, primary: bool = True) -> None:
        """Add a chair to a meeting, potentially making it the primary chair."""
        self.track_nick(nick, messages=0)
        if not nick in self.chairs:
            self.chairs.append(nick)
            self.chairs.sort()
        if primary:
            self.chair = nick

    def remove_chair(self, nick: str) -> None:
        """Remove a chair from a meeting, ignoring requests to remove the founder."""
        if self.founder != nick and nick in self.chairs:
            self.chairs.remove(nick)
        if self.chair not in self.chairs:
            self.chair = self.founder

    def is_chair(self, nick: str) -> bool:
        """Whether a nickname is a chair for the meeting"""
        return nick in self.chairs

    def track_attendee(self, nick: str, alias: Optional[str] = None) -> None:
        """Track an IRC nick as a meeting attendee, optionally assigning an alias."""
        self.aliases[nick] = alias if alias and alias != nick else None
        self.track_nick(nick=nick, messages=0)

    def track_nick(self, nick: str, messages: int = 1) -> None:
        """Track an IRC nick, incrementing its count of messages as indicated"""
        if not nick in self.nicks:
            self.nicks[nick] = 0
        self.nicks[nick] += messages

    def track_message(self, message: Message) -> TrackedMessage:
        """Track a message associated with the meeting."""
        # Per Wikipedia, actions start and end with \x01 (CTRL-A).
        # See "DCC CHAT" under: https://en.wikipedia.org/wiki/Client-to-client_protocol
        # To generate an action in an IRC client like irssi, use /action.
        payload = message.payload.strip(" \x01")
        action = payload[:6] == "ACTION"
        payload = payload[7:].strip() if action else payload.strip()
        tracked = TrackedMessage(id=message.id, timestamp=message.timestamp, action=action, sender=message.nick, payload=payload)
        self.messages.append(tracked)
        self.track_nick(message.nick)
        return tracked

    def track_event(self, event_type: EventType, message: TrackedMessage, operand: Optional[Any] = None) -> TrackedEvent:
        """Track an event associated with a meeting."""
        event = TrackedEvent(event_type=event_type, message=message, operand=operand)
        self.events.append(event)
        return event

    def pop_event(self) -> Optional[TrackedEvent]:
        """Pop the last tracked event off the list of events, if possible, returning the event."""
        # We do not allow the caller to pop the very first event (#startmeeting), because that would leave
        # things in a strange, indeterminate state.  If they don't want the meeting, they should end it.
        return self.events.pop() if len(self.events) > 1 else None
