# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Implementation of meeting commands.
"""

import re
from typing import List, Optional

import attr

from hcoopmeetbotlogic.state import config
from hcoopmeetbotlogic.writer import write_meeting

from .dateutil import formatdate, now
from .interface import Context, Message
from .meeting import EventType, Meeting, TrackedMessage

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

# pylint: disable=unused-argument:
@attr.s
class CommandDispatcher:
    """
    Identify and dispatch meeting commands.

    This is maintained as a class rather than as a set of functions because having
    a class makes certain operations easier - for example, the list_commands() method.
    """

    def list_commands(self) -> List[str]:
        # I've decided to return this in alphabetical order.  There's some case to be made
        # for grouping them together into related commands, but that wouldn't be as straightforward.
        return sorted(["#" + o[len(_METHOD_PREFIX) :] for o in dir(self) if o[: len(_METHOD_PREFIX)] == _METHOD_PREFIX])

    def do_startmeeting(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Start a meeting"""
        if meeting.is_chair(message.sender) and not meeting.active:
            meeting.active = True  # set this here so we can tell this is not a duplicated start meeting event
            meeting.track_event(EventType.START_MEETING, message)
            meeting.original_topic = context.get_topic()
            meeting.meeting_topic = operand
            self._set_channel_topic(meeting, context)
            context.send_reply("Meeting started at %s" % formatdate(meeting.start_time))
            context.send_reply("Current chairs: %s" % ", ".join(meeting.chairs))
            context.send_reply("Useful commands: #action #agreed #help #info #idea #link #topic")

    def do_endmeeting(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """End an active meeting and save to disk."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.END_MEETING, message)
            meeting.end_time = now()
            meeting.active = False
            self._set_channel_topic(meeting, context)
            locations = write_meeting(config=config(), meeting=meeting)
            context.send_reply("Meeting ended at %s" % formatdate(meeting.end_time))
            context.send_reply("Raw log: %s" % locations.log.url)
            context.send_reply("Minutes: %s" % locations.minutes.url)

    def do_save(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Save the meeting to disk in its current state."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.SAVE_MEETING, message)
            locations = write_meeting(config=config(), meeting=meeting)
            context.send_reply("Meeting saved")
            context.send_reply("Raw log: %s" % locations.log.url)
            context.send_reply("Minutes: %s" % locations.minutes.url)

    def do_lurk(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Enable lurk mode, which means to listen without sending any replies."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.LURK, message)
            meeting.lurk = True

    def do_unlurk(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Disable lurk mode, which means to listen without sending any replies."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.UNLURK, message)
            meeting.lurk = False

    def do_meetingtopic(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set a meeting topic, to be included in all sub-topics."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.MEETING_TOPIC, message, meetingtopic=operand)
            meeting.meeting_topic = operand
            self._set_channel_topic(meeting, context)

    def do_topic(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set a new topic in the channel."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.CURRENT_TOPIC, message, topic=operand)
            meeting.current_topic = operand
            self._set_channel_topic(meeting, context)

    def do_chair(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a chair to the meeting."""
        if meeting.is_chair(message.sender):
            chairs = self._tokenize(operand)
            if chairs:
                meeting.track_event(EventType.ADD_CHAIR, message, chairs=chairs)
                for nick in chairs:
                    meeting.add_chair(nick, primary=False)
                context.send_reply("Current chairs: %s" % ", ".join(meeting.chairs))

    def do_unchair(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove a chair from the meeting."""
        if meeting.is_chair(message.sender):
            chairs = self._tokenize(operand)
            if chairs:
                meeting.track_event(EventType.REMOVE_CHAIR, message, chairs=chairs)
                for nick in chairs:
                    meeting.remove_chair(nick)
                context.send_reply("Current chairs: %s" % ", ".join(meeting.chairs))

    def do_nick(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Make the bot aware of a nick which hasn't said anything, for use with actions."""
        nicks = self._tokenize(operand)
        if nicks:
            meeting.track_event(EventType.TRACK_NICK, message, nicks=nicks)
            for nick in nicks:
                meeting.track_nick(nick, messages=0)
            context.send_reply("Current nicks: %s" % ", ".join(meeting.nicks.keys()))

    def do_undo(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove the most recent item from the minutes."""
        if meeting.is_chair(message.sender):
            removed = meeting.pop_event()
            if removed:
                meeting.track_event(EventType.UNDO, message, id=removed.id)
                context.send_reply("Removed event: %s" % removed.display_name())

    def do_meetingname(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set the meeting name, which defaults to the channel name."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.MEETING_NAME, message, meetingname=operand)
            meeting.name = operand
            context.send_reply("Meeting name set to: %s" % operand)

    def do_accepted(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has been accepted."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.ACCEPTED, message, text=operand)

    def do_failed(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has failed."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.FAILED, message, text=operand)

    def do_action(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an action item to the minutes."""
        meeting.track_event(EventType.ACTION, message, text=operand)

    def do_info(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an informational item to the minutes."""
        meeting.track_event(EventType.INFO, message, text=operand)

    def do_idea(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an idea item to the minutes."""
        meeting.track_event(EventType.IDEA, message, text=operand)

    def do_help(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a help item to the minutes."""
        meeting.track_event(EventType.HELP, message, text=operand)

    def do_link(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a link to the minutes."""
        meeting.track_event(EventType.LINK, message, url=operand)

    # These are aliases for the commands above
    do_accept = do_accepted
    do_agree = do_accepted
    do_agreed = do_accepted
    do_fail = do_failed
    do_reject = do_failed
    do_rejected = do_failed

    def _tokenize(self, value: str, pattern: str = r"[\s,]+", limit: Optional[int] = None) -> List[str]:
        """Tokenize a value, splitting via a regular expression and returning all non-empty values up to a limit."""
        if not value or not pattern:
            return []
        else:
            return [token.strip() for token in re.split(pattern, value) if token.strip()][:limit]

    def _set_channel_topic(self, meeting: Meeting, context: Context) -> None:
        """Set the channel topic based on the current state of the meeting."""
        if meeting.active:
            if meeting.meeting_topic and meeting.current_topic:
                context.set_topic("%s (Meeting topic: %s)" % (meeting.current_topic, meeting.meeting_topic))
            elif meeting.meeting_topic:
                context.set_topic("%s" % meeting.meeting_topic)
            elif meeting.current_topic:
                context.set_topic("%s" % meeting.current_topic)
            else:
                context.set_topic("%s" % meeting.display_name())
        else:
            context.set_topic(meeting.original_topic if meeting.original_topic else "")


# Singleton command dispatcher
_DISPATCHER = CommandDispatcher()


def list_commands() -> List[str]:
    """List available commands."""
    return _DISPATCHER.list_commands()


def dispatch(meeting: Meeting, context: Context, message: TrackedMessage) -> None:
    """Dispatch any command contained in the message to the dispatcher method with the matching name."""
    operation_match = _OPERATION_REGEX.match(message.payload)
    url_match = _URL_REGEX.match(message.payload)
    if operation_match:
        operation = operation_match.group(_OPERATION_GROUP).lower().strip()
        operand = operation_match.group(_OPERAND_GROUP).strip()
        if hasattr(_DISPATCHER, "%s%s" % (_METHOD_PREFIX, operation)):
            getattr(_DISPATCHER, "%s%s" % (_METHOD_PREFIX, operation))(meeting, context, operation, operand, message)
    elif url_match:
        # as a special case, turns messages that start with a URL into a link operation
        operation = "link"
        operand = url_match.group(_URL_GROUP)
        _DISPATCHER.do_link(meeting, context, operation, operand, message)


def is_startmeeting(message: Message) -> bool:
    """Whether the message contains a start-of-meeting indicator."""
    return bool(message.payload and _STARTMEETING_REGEX.match(message.payload))
