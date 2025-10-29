# vim: set ft=python ts=4 sw=4 expandtab:

"""
Meeting state.
"""

import json
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

import cattrs
from attrs import define, field, frozen

from hcoopmeetbotlogic.dateutil import formatdate, now
from hcoopmeetbotlogic.interface import Message


class _CattrConverter(cattrs.GenConverter):
    """
    Cattr converter to serialize Meeting to and from JSON.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_unstructure_hook(datetime, lambda d: d.isoformat() if d else None)
        self.register_structure_hook(datetime, lambda s, _: datetime.fromisoformat(s) if s else None)


_CONVERTER = _CattrConverter()

# Note: we use (str, Enum) so that the enum value gets serialized rather than the enum name


class EventType(StrEnum):
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


class VotingAction(StrEnum):
    """Voting actions"""

    IN_FAVOR = "+1"
    OPPOSED = "-1"


@frozen
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

    id: str
    sender: str
    payload: str
    action: bool
    timestamp: datetime

    def display_name(self) -> str:
        """Get the message display name."""
        return f"{self.id}@{formatdate(self.timestamp)}"


@frozen
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

    event_type: EventType
    message: TrackedMessage
    operand: Any | None
    id: str = field()
    timestamp: datetime = field()

    # noinspection PyUnresolvedReferences
    @id.default  # noqa: A003
    def _default_id(self) -> str:
        return self.message.id

    # noinspection PyUnresolvedReferences
    @timestamp.default
    def _default_timestamp(self) -> datetime:
        return self.message.timestamp

    def display_name(self) -> str:
        """Get the event display name."""
        return f"{self.id}@{formatdate(self.timestamp)}"


@define(slots=False)
class Meeting:
    # noinspection PyUnresolvedReferences
    """
    A meeting on a particular IRC channel.

    The meeting can be serialized and deserialized to and from JSON.  This is the mechanism we use
    to persist the raw log to disk.  If you round trip the JSON (generate JSON and then use that
    JSON to create a new meeting), the resulting object contains data that is equivalent, but not
    exactly identical to, the original object.  Each tracked event has an associated message.  In
    the original object, the tracked event always refers to one of the message objects that is
    already in the messages list.  When you deserialize from JSON, the object in the message list
    will be different than the one on the tracked event, although they will be equivalent by value.
    So, if you deserialize from JSON, it's best to treat the resulting object as a read-only copy.
    The copy won't always work exactly like a meeting that was created at runtime based on actual
    IRC traffic.

    Attributes:
        id(str): Unique identifier for the meeting
        name(str): The name of the meeting, which defaults to the channel name
        founder(str): IRC nick of the meeting founder, always a member of chairs
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

    founder: str = field()
    channel: str = field()
    network: str = field()
    id: str = field(factory=lambda: uuid.uuid4().hex)
    name: str = field()
    chair: str = field()
    chairs: list[str] = field()
    nicks: dict[str, int] = field()
    start_time: datetime = field(factory=now)
    end_time: datetime | None = None
    active: bool = False
    original_topic: str | None = None
    current_topic: str | None = None
    messages: list[TrackedMessage] = field(factory=list)
    events: list[TrackedEvent] = field(factory=list)
    aliases: dict[str, str | None] = field(factory=dict)
    vote_in_progress: bool = False
    motion_index: int | None = None

    # noinspection PyUnresolvedReferences
    @chair.default
    def _default_chair(self) -> str:
        return self.founder

    # noinspection PyUnresolvedReferences
    @chairs.default
    def _default_chairs(self) -> list[str]:
        return [self.chair]

    # noinspection PyUnresolvedReferences
    @nicks.default
    def _default_nicks(self) -> dict[str, int]:
        return dict.fromkeys(self.chairs, 0)

    # noinspection PyUnresolvedReferences
    @name.default
    def _default_meeting_name(self) -> str:
        return self.channel

    @staticmethod
    def meeting_key(channel: str, network: str) -> str:
        """Build the dict key for a network and channel."""
        return f"{channel}/{network}"

    def to_json(self) -> str:
        """Serialize a meeting to JSON."""
        return json.dumps(_CONVERTER.unstructure(self), indent="  ")

    @staticmethod
    def from_json(data: str) -> "Meeting":
        """Deserialize a meeting from JSON."""
        return _CONVERTER.structure(json.loads(data), Meeting)

    def key(self) -> str:
        return Meeting.meeting_key(self.channel, self.network)

    def display_name(self) -> str:
        """Get the meeting display name."""
        return f"{self.channel}/{self.network}@{formatdate(self.start_time)}"

    def add_chair(self, nick: str, *, primary: bool = True) -> None:
        """Add a chair to a meeting, potentially making it the primary chair."""
        self.track_nick(nick, messages=0)
        if nick not in self.chairs:
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

    def track_attendee(self, nick: str, alias: str | None = None) -> None:
        """Track an IRC nick as a meeting attendee, optionally assigning an alias."""
        self.aliases[nick] = alias if alias and alias != nick else None
        self.track_nick(nick=nick, messages=0)

    def track_nick(self, nick: str, messages: int = 1) -> None:
        """Track an IRC nick, incrementing its count of messages as indicated"""
        if nick not in self.nicks:
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

    def track_event(self, event_type: EventType, message: TrackedMessage, operand: Any | None = None) -> TrackedEvent:
        """Track an event associated with a meeting."""
        event = TrackedEvent(event_type=event_type, message=message, operand=operand)
        self.events.append(event)
        return event

    def pop_event(self) -> TrackedEvent | None:
        """Pop the last tracked event off the list of events, if possible, returning the event."""
        # We do not allow the caller to pop the very first event (#startmeeting), because that would leave
        # things in a strange, indeterminate state.  If they don't want the meeting, they should end it.
        return self.events.pop() if len(self.events) > 1 else None
