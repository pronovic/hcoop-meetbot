# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Writes meeting log and minutes to disk.
"""

from __future__ import annotations

import os
import re
from enum import Enum
from typing import Any, Dict, List, Optional, TextIO

from attrs import field, frozen
from genshi.builder import Element, tag
from genshi.template import MarkupTemplate, TemplateLoader

from .config import Config, OutputFormat
from .dateutil import formatdate
from .location import Locations, derive_locations
from .meeting import EventType, Meeting, TrackedMessage
from .release import DATE, URL, VERSION

# Location of Genshi templates
_TEMPLATES = os.path.join(os.path.dirname(__file__), "templates")
_LOADER = TemplateLoader(search_path=_TEMPLATES, auto_reload=False)

# Standard date and time formats
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"
_TIME_FORMAT = "%H:%M:%S"

# Identifies a message that contains an operation
_OPERATION_REGEX = re.compile(r"(^\s*)(#\w+)(\s*)(.*$)", re.IGNORECASE)
_OPERATION_GROUP = 2
_OPERAND_GROUP = 4

# Pulls a URL out of a LINK event
_URL_REGEX = re.compile(r"(^.*)((http|https|irc|ftp|mailto|ssh)(://)([^\s]*))(.*$)")
_URL_GROUP = 2

# Identifies a nick at the front of the payload, to be highlighted
_NICK_REGEX = re.compile(r"(^[^\s]+:(?!//))")  # note: lookback (?!//) prevents us from matching URLs

# List of event types that are excluded from the summary in the meeting minutes
_EXCLUDED = [
    EventType.START_MEETING,
    EventType.END_MEETING,
    EventType.UNDO,
    EventType.SAVE_MEETING,
    EventType.TRACK_NICK,
    EventType.ADD_CHAIR,
    EventType.REMOVE_CHAIR,
    EventType.ATTENDEE,
]


@frozen
class _LogMessage:
    """A rendered version of a message in the log."""

    # This is difficult to accomplish directly in a Genshi template, so instead we're
    # generating HTML manually.  Note that we always use Genshi's Element object (via
    # genshi.tag) rather than directly concatenating together HTML strings.  This helps
    # avoid problems with cross-site scripting and similar vulnerabilities. For instance,
    # if someone pastes Javascript into an IRC conversation, that Javascript will show up
    # as literal text in the raw log - it won't be rendered or executed.

    id: Element
    timestamp: Element
    nick: Element
    content: Element

    @staticmethod
    def for_message(config: Config, message: TrackedMessage) -> _LogMessage:
        return _LogMessage(
            id=_LogMessage._id(message),
            timestamp=_LogMessage._timestamp(config, message),
            nick=_LogMessage._nick(message),
            content=_LogMessage._content(message),
        )

    @staticmethod
    def _id(message: TrackedMessage) -> Element:
        return tag.a(name=message.id)

    @staticmethod
    def _timestamp(config: Config, message: TrackedMessage) -> Element:
        formatted = formatdate(timestamp=message.timestamp, zone=config.timezone, fmt=_TIME_FORMAT)
        return tag.span(formatted, class_="tm")

    @staticmethod
    def _nick(message: TrackedMessage) -> Element:
        spanclass = "nka" if message.action else "nk"
        content = "<%s>" % message.sender
        return tag.span(content, class_=spanclass)

    @staticmethod
    def _content(message: TrackedMessage) -> Element:
        if message.action:
            return tag.span(_LogMessage._payload(message.payload), class_="ac")
        else:
            operation_match = _OPERATION_REGEX.match(message.payload)
            if operation_match:
                operation = operation_match.group(_OPERATION_GROUP).lower().strip()
                operand = operation_match.group(_OPERAND_GROUP).strip()
                if operation == "#topic":
                    return tag.span(
                        tag.span("%s " % operation, class_="topic"), tag.span(_LogMessage._payload(operand), class_="topicline")
                    )
                else:
                    return tag.span(
                        tag.span("%s " % operation, class_="cmd"), tag.span(_LogMessage._payload(operand), class_="cmdline")
                    )
            else:
                return _LogMessage._payload(message.payload)

    @staticmethod
    def _payload(payload: str) -> Element:
        return tag.span(
            [
                tag.span(element, class_="hi") if _NICK_REGEX.fullmatch(element) else tag.span(element)
                for element in _NICK_REGEX.split(payload, 1)
                if element
            ]
        )


@frozen
class _MeetingAction:
    """An action assigned to a meeting attendee."""

    id: str
    text: str


@frozen
class _MeetingAttendee:
    """A meeting attendee, including count of chat lines and all associated actions."""

    nick: str
    alias: Optional[str]
    count: int
    percentage: str  # stored as a string so we control rounding and format
    actions: List[_MeetingAction]


@frozen
class _AliasMatcher:
    """Utility class to identify whether an attendee nick or alias is found in a message."""

    nick: str
    alias: Optional[str]
    nick_pattern: re.Pattern = field()
    alias_pattern: Optional[re.Pattern] = field()

    @nick_pattern.default
    def _nick_pattern_default(self) -> re.Pattern:
        return _AliasMatcher._regex(self.nick)

    @alias_pattern.default
    def _alias_pattern_default(self) -> Optional[re.Pattern]:
        return _AliasMatcher._regex(self.alias) if self.alias else None

    @staticmethod
    def _regex(identifier) -> re.Pattern:
        escaped = re.escape(identifier)
        regex = r"(^|\s)(%s|%s:|\(%s\))($|\s)" % (escaped, escaped, escaped)
        return re.compile(regex, re.IGNORECASE)

    def matches(self, message: str) -> bool:
        """Return true if the attendee nick or alias is found in the message."""
        return bool(self.nick_pattern.search(message)) or (self.alias_pattern and self.alias_pattern.search(message))


@frozen
class _MeetingEvent:
    """A meeting event tied to a topic."""

    id: str
    event_type: str
    timestamp: str
    nick: str
    payload: str
    link: Optional[str] = None


@frozen
class _MeetingTopic:
    """A meeting topic within the minutes, including all of the events tied to it."""

    id: str
    name: str
    timestamp: str
    nick: str
    events: List[_MeetingEvent] = field(factory=list)


@frozen
class _MeetingMinutes:
    """A summarized version of the meeting minutes."""

    start_time: str
    end_time: str
    founder: str
    actions: List[_MeetingAction]
    attendees: List[_MeetingAttendee]
    topics: List[_MeetingTopic]

    @staticmethod
    def for_meeting(config: Config, meeting: Meeting) -> _MeetingMinutes:
        return _MeetingMinutes(
            start_time=formatdate(timestamp=meeting.start_time, zone=config.timezone, fmt=_DATE_FORMAT),
            end_time=formatdate(timestamp=meeting.end_time, zone=config.timezone, fmt=_DATE_FORMAT),
            founder=meeting.founder,
            actions=_MeetingMinutes._actions(meeting),
            attendees=_MeetingMinutes._attendees(meeting),
            topics=_MeetingMinutes._topics(config, meeting),
        )

    @staticmethod
    def _actions(meeting: Meeting) -> List[_MeetingAction]:
        actions = []
        for event in meeting.events:
            if event.event_type == EventType.ACTION and event.operand:
                action = _MeetingAction(id="action-%s" % event.id, text=event.operand)
                actions.append(action)
        return actions

    @staticmethod
    def _attendees(meeting: Meeting) -> List[_MeetingAttendee]:
        attendees = []
        total = sum(meeting.nicks.values())
        for nick in sorted(meeting.nicks.keys()):
            count = meeting.nicks[nick]
            percentage = "%d" % (round(count / total * 100.0) if total > 0.0 else 0.0)
            alias = meeting.aliases[nick] if nick in meeting.aliases else None
            actions = _MeetingMinutes._attendee_actions(meeting, nick, alias)
            attendee = _MeetingAttendee(nick=nick, alias=alias, count=count, percentage=percentage, actions=actions)
            attendees.append(attendee)
        return attendees

    @staticmethod
    def _attendee_actions(meeting: Meeting, nick: str, alias: Optional[str]) -> List[_MeetingAction]:
        actions = []
        matcher = _AliasMatcher(nick, alias)
        for event in meeting.events:
            if event.event_type == EventType.ACTION and event.operand:
                if matcher.matches(event.operand):
                    action = _MeetingAction(id="action-%s" % event.id, text=event.operand)
                    actions.append(action)
        return actions

    @staticmethod
    def _topics(config: Config, meeting: Meeting) -> List[_MeetingTopic]:
        current = _MeetingTopic(
            id=meeting.messages[0].id,
            name="Prologue",
            timestamp=formatdate(timestamp=meeting.messages[0].timestamp, zone=config.timezone, fmt=_TIME_FORMAT),
            nick=meeting.founder,
            events=[],
        )
        topics = [current]
        for event in meeting.events:
            if event.event_type == EventType.TOPIC:
                current = _MeetingTopic(
                    id=event.id,
                    name="%s" % event.operand,
                    timestamp=formatdate(timestamp=event.timestamp, zone=config.timezone, fmt=_TIME_FORMAT),
                    nick=event.message.sender,
                )
                topics.append(current)
            elif event.event_type == EventType.LINK:
                url_match = _URL_REGEX.match("%s" % event.operand)
                item = _MeetingEvent(
                    id=event.id,
                    event_type=event.event_type.value,
                    timestamp=formatdate(timestamp=event.timestamp, zone=config.timezone, fmt=_TIME_FORMAT),
                    nick=event.message.sender,
                    payload="%s" % event.operand,
                    link=url_match.group(_URL_GROUP) if url_match else None,
                )
                current.events.append(item)
            elif event.event_type not in _EXCLUDED:  # some things are adminstrative and aren't relevant
                item = _MeetingEvent(
                    id=event.id,
                    event_type=event.event_type.value,
                    timestamp=formatdate(timestamp=event.timestamp, zone=config.timezone, fmt=_TIME_FORMAT),
                    nick=event.message.sender,
                    payload=event.operand.value if isinstance(event.operand, Enum) else "%s" % event.operand,
                )
                current.events.append(item)
        if not topics[0].events:
            del topics[0]  # get rid of the prologue unless we actually used it
        return topics


def _render_html(template: str, context: Dict[str, Any], out: TextIO) -> None:
    """Render the named template to HTML, writing into the provided file."""
    renderer = _LOADER.load(filename=template, cls=MarkupTemplate)  # type: MarkupTemplate
    renderer.generate(**context).render(method="html", doctype="html", out=out)


def write_raw_log(config: Config, locations: Locations, meeting: Meeting) -> None:  # pylint: disable=unused-argument:
    """Write the raw meeting log to disk in JSON format."""
    os.makedirs(os.path.dirname(locations.raw_log.path), exist_ok=True)
    with open(locations.raw_log.path, "w", encoding="utf-8") as out:
        out.write(meeting.to_json())


def write_formatted_log(config: Config, locations: Locations, meeting: Meeting) -> None:
    """Write the formatted meeting log to disk."""
    context = {
        "title": "%s Log" % meeting.name,
        "messages": [_LogMessage.for_message(config, message) for message in meeting.messages],
    }
    os.makedirs(os.path.dirname(locations.formatted_log.path), exist_ok=True)
    with open(locations.formatted_log.path, "w", encoding="utf-8") as out:
        if config.output_format == OutputFormat.HTML:
            _render_html(template="log.html", context=context, out=out)
        else:
            raise ValueError("Unsupported output format: %s" % config.output_format)


def write_formatted_minutes(config: Config, locations: Locations, meeting: Meeting) -> None:
    """Write the formatted meeting minutes to disk."""
    context = {
        "title": "%s Minutes" % meeting.name,
        "software": {"version": VERSION, "url": URL, "date": DATE},
        "logpath": os.path.basename(locations.formatted_log.path),
        "minutes": _MeetingMinutes.for_meeting(config, meeting),
    }
    os.makedirs(os.path.dirname(locations.formatted_minutes.path), exist_ok=True)
    with open(locations.formatted_minutes.path, "w", encoding="utf-8") as out:
        if config.output_format == OutputFormat.HTML:
            _render_html(template="minutes.html", context=context, out=out)
        else:
            raise ValueError("Unsupported output format: %s" % config.output_format)


def write_meeting(config: Config, meeting: Meeting) -> Locations:
    """Write meeting files to disk, returning the file locations."""
    locations = derive_locations(config, meeting)
    write_raw_log(config, locations, meeting)
    write_formatted_log(config, locations, meeting)
    write_formatted_minutes(config, locations, meeting)
    return locations
