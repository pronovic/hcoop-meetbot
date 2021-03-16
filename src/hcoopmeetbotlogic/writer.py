# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Writes meeting log and minutes to disk.
"""

# Note that we always use Genshi's Element object (via genshi.tag) rather than manually
# generating HTML strings.  This helps avoid various kinds of injection vulnerabilities.
# For instance, if someone pastes Javascript into an IRC conversation, that Javascript
# will show up as literal text in the raw log - it won't be rendered or executed.

from __future__ import annotations

import os
import re
from typing import Any, Dict, TextIO

import attr
from genshi.builder import Element, tag
from genshi.template import MarkupTemplate, TemplateLoader

from .config import Config
from .dateutil import formatdate
from .location import Location, Locations, derive_locations
from .meeting import Meeting, TrackedMessage

# Location of Genshi templates
_TEMPLATES = os.path.join(os.path.dirname(__file__), "templates")
_LOADER = TemplateLoader(search_path=_TEMPLATES, auto_reload=False)

# Identifies a message that contains an operation
_OPERATION_REGEX = re.compile(r"(^\s*)(#)(\w+)(\s*)(.*$)", re.IGNORECASE)
_OPERATION_GROUP = 3
_OPERAND_GROUP = 5

# Identifies a highlight within a message payload (finds cases of "nick:" to be highlighted)
_HIGHLIGHT_REGEX = re.compile(r"[^\s]+:")


@attr.s(frozen=True)
class _LogMessage:
    """A rendered version of a message in the log."""

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
        formatted = formatdate(timestamp=message.timestamp, zone=config.timezone, fmt="%H:%M:%S")
        return tag.span(formatted, class_="tm")

    @staticmethod
    def _nick(message: TrackedMessage) -> Element:
        spanclass = "nka" if message.action else "nk"
        content = "<%s>" % message.sender
        return tag.span(content, class_=spanclass)

    @staticmethod
    def _content(message: TrackedMessage) -> Element:
        if message.action:
            return tag.span(message.payload, class_="ac")
        else:
            operation_match = _OPERATION_REGEX.match(message.payload)
            if operation_match:
                operation = operation_match.group(_OPERATION_GROUP).lower().strip()
                operand = operation_match.group(_OPERAND_GROUP).strip()
                if operation == "#topic":
                    return tag.span(
                        tag.span(operation, class_="topic"), tag.span(_LogMessage._payload(operand), class_="topicline")
                    )
                else:
                    return tag.span(tag.span(operation, class_="cmd"), tag.span(_LogMessage._payload(operand), class_="cmdline"))
            else:
                return _LogMessage._payload(message.payload)

    @staticmethod
    def _payload(payload: str) -> Element:
        return tag.span(
            [
                tag.span(element, class_="hi") if _HIGHLIGHT_REGEX.fullmatch(element) else tag.span(element.strip())
                for element in _HIGHLIGHT_REGEX.split(payload)
            ]
        )


def _render_html(template: str, context: Dict[str, Any], out: TextIO) -> None:
    """Render the named template to HTML, writing into the provided file."""
    renderer = _LOADER.load(filename=template, cls=MarkupTemplate)  # type: MarkupTemplate
    renderer.generate(**context).render(method="html", doctype="html", out=out)


def _write_log(config: Config, location: Location, meeting: Meeting) -> None:
    """Write the meeting log to disk."""
    context = {
        "title": "%s Log" % meeting.name,
        "messages": [_LogMessage.for_message(config, message) for message in meeting.messages],
    }
    with open(location.path, "x") as out:
        _render_html(template="log.genshi", context=context, out=out)


# TODO: remove unused-argument
def _write_minutes(config: Config, location: Location, meeting: Meeting) -> None:  # pylint: disable=unused-argument:
    """Write the meeting minutes to disk."""
    with open(location.path, "x") as out:
        _render_html(template="minutes.genshi", context={}, out=out)


def write_meeting(config: Config, meeting: Meeting) -> Locations:
    """Write meeting files to disk, returning the file locations."""
    locations = derive_locations(config, meeting)
    _write_log(config, locations.log, meeting)
    _write_minutes(config, locations.minutes, meeting)
    return locations
