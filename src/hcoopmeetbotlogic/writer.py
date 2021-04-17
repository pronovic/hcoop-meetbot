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

import attr
from genshi.builder import Element, tag
from genshi.template import MarkupTemplate, TemplateLoader

from .config import Config
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
]


@attr.s(frozen=True)
class _LogMessage:
    """A rendered version of a message in the log."""

    # This is difficult to accomplish directly in a Genshi template, so instead we're
    # generating HTML manually.  Note that we always use Genshi's Element object (via
    # genshi.tag) rather than directly concatenating together HTML strings.  This helps
    # avoid problems with cross-site scripting and similar vulnerabilities. For instance,
    # if someone pastes Javascript into an IRC conversation, that Javascript will show up
    # as literal text in the raw log - it won't be rendered or executed.

    id = attr.ib(type=Element)
    timestamp = attr.ib(type=Element)
    nick = attr.ib(type=Element)
    content = attr.ib(type=Element)

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


@attr.s(frozen=True)
class _MeetingAttendee:
    """A meeting attendee, including count of chat lines and all associated actions."""

    nick = attr.ib(type=str)
    alias = attr.ib(type=Optional[str])
    count = attr.ib(type=int)
    actions = attr.ib(type=List[str])


@attr.s(frozen=True)
class _MeetingEvent:
    """A meeting event tied to a topic."""

    id = attr.ib(type=str)
    event_type = attr.ib(type=str)
    timestamp = attr.ib(type=str)
    nick = attr.ib(type=str)
    payload = attr.ib(type=str)
    link = attr.ib(type=Optional[str], default=None)


@attr.s(frozen=True)
class _MeetingTopic:
    """A meeting topic within the minutes, including all of the events tied to it."""

    id = attr.ib(type=str)
    name = attr.ib(type=str)
    timestamp = attr.ib(type=str)
    nick = attr.ib(type=str)
    events = attr.ib(type=List[_MeetingEvent])

    @events.default
    def _default_events(self) -> List[_MeetingEvent]:
        return []


@attr.s(frozen=True)
class _MeetingMinutes:
    """A summarized version of the meeting minutes."""

    start_time = attr.ib(type=str)
    end_time = attr.ib(type=str)
    founder = attr.ib(type=str)
    actions = attr.ib(type=List[str])
    attendees = attr.ib(type=List[_MeetingAttendee])
    topics = attr.ib(type=List[_MeetingTopic])

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
    def _actions(meeting: Meeting) -> List[str]:
        return [event.operand for event in meeting.events if event.event_type == EventType.ACTION and event.operand]

    @staticmethod
    def _attendees(meeting: Meeting) -> List[_MeetingAttendee]:
        attendees = []
        for nick in sorted(meeting.nicks.keys()):
            count = meeting.nicks[nick]
            alias = meeting.aliases[nick] if nick in meeting.aliases else None
            actions = _MeetingMinutes._attendee_actions(meeting, nick, alias)
            attendee = _MeetingAttendee(nick=nick, alias=alias, count=count, actions=actions)
            attendees.append(attendee)
        return attendees

    @staticmethod
    def _attendee_actions(meeting: Meeting, nick: str, alias: Optional[str]) -> List[str]:
        actions = []
        nick_pattern = re.compile(r"\b%s\b" % nick, re.IGNORECASE)
        alias_pattern = re.compile(r"\b%s\b" % alias, re.IGNORECASE) if alias else None
        for event in meeting.events:
            if event.event_type == EventType.ACTION and event.operand:
                if nick_pattern.search(event.operand) or (alias_pattern and alias_pattern.search(event.operand)):
                    actions.append(event.operand)
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


def _write_log(config: Config, locations: Locations, meeting: Meeting) -> None:
    """Write the meeting log to disk."""
    context = {
        "title": "%s Log" % meeting.name,
        "messages": [_LogMessage.for_message(config, message) for message in meeting.messages],
    }
    os.makedirs(os.path.dirname(locations.log.path), exist_ok=True)
    with open(locations.log.path, "w") as out:
        _render_html(template="log.html", context=context, out=out)


def _write_minutes(config: Config, locations: Locations, meeting: Meeting) -> None:
    """Write the meeting minutes to disk."""
    context = {
        "title": "%s Minutes" % meeting.name,
        "software": {"version": VERSION, "url": URL, "date": DATE},
        "logpath": os.path.basename(locations.log.path),
        "minutes": _MeetingMinutes.for_meeting(config, meeting),
    }
    os.makedirs(os.path.dirname(locations.minutes.path), exist_ok=True)
    with open(locations.minutes.path, "w") as out:
        _render_html(template="minutes.html", context=context, out=out)


def write_meeting(config: Config, meeting: Meeting) -> Locations:
    """Write meeting files to disk, returning the file locations."""
    locations = derive_locations(config, meeting)
    _write_log(config, locations, meeting)
    _write_minutes(config, locations, meeting)
    return locations
