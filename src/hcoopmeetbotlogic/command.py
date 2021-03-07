# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Implementation of meeting commands.
"""

import re
from typing import List

import attr

from .interface import Message
from .meeting import Meeting, TrackedMessage

# Regular expression to identify the startmeeting command
_STARTMEETING_REGEX = re.compile(r"(^\s*)(#)(startmeeting)(\s*)(.*$)", re.IGNORECASE)

# Regular expression to identify a command in a message
_OPERATION_REGEX = re.compile(r"(^\s*)(#)(\w+)(\s*)(.*$)", re.IGNORECASE)
_OPERATION_GROUP = 3
_OPERAND_GROUP = 5

# Regular expression to identify a message that starts with a URL
_URL_REGEX = re.compile(r"(^\s*)((http|https|irc|ftp|mailto|ssh)(://)([^\s]*))(.*$)")
_URL_GROUP = 2

# Prefix of a method on CommandDispatcher that implements a command
_METHOD_PREFIX = "do_"


@attr.s
class CommandDispatcher:
    """
    Identify and dispatch meeting commands.

    This is maintained as a class rather than as function in this module because
    having a class makes certain operations - like for list_command() - easier.
    """

    def list_commands(self) -> List[str]:
        # I've decided to return this in alphabetical order.  There's some case to be made
        # for grouping them together into related commands, but that wouldn't be as straightforward.
        return sorted(["#" + o[len(_METHOD_PREFIX) :] for o in dir(self) if o[: len(_METHOD_PREFIX)] == _METHOD_PREFIX])

    def do_startmeeting(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Start a meeting"""

    def do_endmeeting(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """End an active meeting and save to disk."""

    def do_topic(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set a new topic in the channel."""

    def do_meetingtopic(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set a meeting topic, to be included in all sub-topics."""

    def do_accepted(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has been accepted."""

    def do_failed(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has failed."""

    def do_chair(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a chair to the meeting."""

    def do_unchair(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove a chair from the meeting."""
        # Note: founder cannot be removed

    def do_undo(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove the most recent item from the minutes."""

    def do_meetingname(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set the meeting name, used when saving to disk."""

    def do_action(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an action item to the minutes."""

    def do_nick(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Make the bot aware of a nick which hasn't said anything, for use with actions."""

    def do_info(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an informational item to the minutes."""

    def do_idea(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an idea item to the minutes."""

    def do_help(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a help item to the minutes."""

    def do_link(self, meeting: Meeting, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a link to the minutes."""

    # These are aliases for the commands above
    do_accept = do_accepted
    do_agree = do_accepted
    do_agreed = do_accepted
    do_fail = do_failed
    do_reject = do_failed
    do_rejected = do_failed


# Singleton command dispatcher
_DISPATCHER = CommandDispatcher()


def list_commands() -> List[str]:
    """List available commands."""
    # noinspection PyTypeChecker
    return _DISPATCHER.list_commands()


def dispatch(meeting: Meeting, message: TrackedMessage) -> None:
    """Dispatch any command contained in the message to the dispatcher method with the matching name."""
    operation_match = _OPERATION_REGEX.match(message.payload)
    url_match = _URL_REGEX.match(message.payload)
    if operation_match:
        operation = operation_match.group(_OPERATION_GROUP).lower().strip()
        operand = operation_match.group(_OPERAND_GROUP).strip()
        if hasattr(_DISPATCHER, "%s%s" % (_METHOD_PREFIX, operation)):
            getattr(_DISPATCHER, "%s%s" % (_METHOD_PREFIX, operation))(meeting, operation, operand, message)
    elif url_match:
        # as a special case, turns messages that start with a URL into a link operation
        operation = "link"
        operand = url_match.group(_URL_GROUP)
        _DISPATCHER.do_link(meeting, operation, operand, message)


def is_startmeeting(message: Message) -> bool:
    """Whether the message contains a start-of-meeting indicator."""
    return bool(message.payload and _STARTMEETING_REGEX.match(message.payload))
