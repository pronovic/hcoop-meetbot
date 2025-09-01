# vim: set ft=python ts=4 sw=4 expandtab:
# ruff: noqa: ARG002,PLR6301,PLR0904

"""
Implementation of meeting commands.
"""

import re
from datetime import datetime

from attrs import define

from hcoopmeetbotlogic.dateutil import formatdate, now
from hcoopmeetbotlogic.interface import Context, Message
from hcoopmeetbotlogic.meeting import EventType, Meeting, TrackedMessage, VotingAction
from hcoopmeetbotlogic.release import DOCS
from hcoopmeetbotlogic.state import config, deactivate_meeting
from hcoopmeetbotlogic.writer import write_meeting

# Regular expression to identify the startmeeting command
_STARTMEETING_REGEX = re.compile(r"(^\s*)(#)(startmeeting)(\s*)(.*$)", re.IGNORECASE)

# Regular expression to identify a command in a message
_OPERATION_REGEX = re.compile(r"(^\s*)(#)([a-zA-Z_]+)($|\s+)(.*$)", re.IGNORECASE)
_OPERATION_GROUP = 3
_OPERAND_GROUP = 5

# Regular expression to identify a message that starts with a URL
_URL_REGEX = re.compile(r"(^\s*)((http|https|irc|ftp|mailto|ssh)(://)([^\s]*))(.*$)")
_URL_GROUP = 2

# Prefix of a method on CommandDispatcher that implements a command
_METHOD_PREFIX = "do_"


# noinspection PyMethodMayBeStatic
@define
class CommandDispatcher:
    """
    Identify and dispatch meeting commands.

    This is maintained as a class rather than as a set of functions because having
    a class makes certain operations easier - for example, the list_commands() method.
    """

    def list_commands(self) -> list[str]:
        # I've decided to return this in alphabetical order.  There's some case to be made
        # for grouping them together into related commands, but that wouldn't be as straightforward.
        return sorted(["#" + o[len(_METHOD_PREFIX) :] for o in dir(self) if o[: len(_METHOD_PREFIX)] == _METHOD_PREFIX])

    def do_startmeeting(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Start a meeting"""
        if meeting.is_chair(message.sender) and not meeting.active:
            meeting.active = True  # set this here so we can tell this is not a duplicated start meeting event
            meeting.track_event(EventType.START_MEETING, message)
            meeting.original_topic = context.get_topic()
            self._set_channel_topic(meeting, context)
            context.send_reply(f"Meeting started at {self._formatdate(meeting.start_time)}")
            context.send_reply(f"Current chairs: {', '.join(meeting.chairs)}")
            context.send_reply("Useful commands: #action #info #idea #link #topic #motion #vote #close #endmeeting")
            context.send_reply(f"See also: {DOCS}")
            context.send_reply("Participants should now identify themselves with '#here' or with an alias like '#here FirstLast'")

    def do_endmeeting(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """End an active meeting and save to disk."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.END_MEETING, message)
            meeting.end_time = now()
            meeting.active = False
            self._set_channel_topic(meeting, context)
            locations = write_meeting(config=config(), meeting=meeting)
            context.send_reply(f"Meeting ended at {self._formatdate(meeting.end_time)}")
            context.send_reply(f"Raw log: {locations.raw_log.url}")
            context.send_reply(f"Formatted log: {locations.formatted_log.url}")
            context.send_reply(f"Minutes: {locations.formatted_minutes.url}")
            deactivate_meeting(meeting, retain=True)

    def do_save(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Save the meeting to disk in its current state."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.SAVE_MEETING, message)
            locations = write_meeting(config=config(), meeting=meeting)
            context.send_reply("Meeting saved")
            context.send_reply(f"Raw log: {locations.raw_log.url}")
            context.send_reply(f"Formatted log: {locations.formatted_log.url}")
            context.send_reply(f"Minutes: {locations.formatted_minutes.url}")

    def do_topic(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set a new topic in the channel."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.TOPIC, message, operand=operand)
            meeting.current_topic = operand
            self._set_channel_topic(meeting, context)

    def do_chair(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a chair to the meeting."""
        if meeting.is_chair(message.sender):
            chairs = self._tokenize(operand)
            if chairs:
                meeting.track_event(EventType.ADD_CHAIR, message, operand=chairs)
                for nick in chairs:
                    meeting.add_chair(nick, primary=False)
                context.send_reply(f"Current chairs: {', '.join(meeting.chairs)}")

    def do_unchair(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove a chair from the meeting."""
        if meeting.is_chair(message.sender):
            chairs = self._tokenize(operand)
            if chairs:
                meeting.track_event(EventType.REMOVE_CHAIR, message, operand=chairs)
                for nick in chairs:
                    meeting.remove_chair(nick)
                context.send_reply(f"Current chairs: {', '.join(meeting.chairs)}")

    def do_here(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Document attendance and optionally associate a nick with an alias, for use with actions."""
        alias = operand or message.sender
        meeting.track_event(EventType.ATTENDEE, message, operand=alias)
        meeting.track_attendee(nick=message.sender, alias=alias)

    def do_nick(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Make the bot aware of a nick which hasn't said anything, for use with actions."""
        nicks = self._tokenize(operand)
        if nicks:
            meeting.track_event(EventType.TRACK_NICK, message, operand=nicks)
            for nick in nicks:
                meeting.track_nick(nick, messages=0)
            context.send_reply(f"Current nicks: {', '.join(meeting.nicks.keys())}")

    def do_undo(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Remove the most recent item from the minutes."""
        if meeting.is_chair(message.sender):
            removed = meeting.pop_event()
            if removed:
                meeting.track_event(EventType.UNDO, message, operand=removed.id)
                context.send_reply(f"Removed event: {removed.display_name()}")

    def do_meetingname(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Set the meeting name, which defaults to the channel name."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.MEETING_NAME, message, operand=operand)
            meeting.name = operand
            context.send_reply(f"Meeting name set to: {operand}")

    def do_motion(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Open a motion."""
        if meeting.is_chair(message.sender):
            meeting.track_event(EventType.MOTION, message, operand=operand)
            meeting.vote_in_progress = True
            meeting.motion_index = len(meeting.events) - 1
            context.send_reply("Voting is open")

    def do_vote(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Record a vote."""
        if meeting.vote_in_progress:
            action = VotingAction.IN_FAVOR if operand.startswith("+") else VotingAction.OPPOSED
            meeting.track_event(EventType.VOTE, message, operand=action)
        else:
            context.send_reply("No vote is in progress")

    def do_close(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Close a motion."""
        if meeting.is_chair(message.sender) and meeting.vote_in_progress:
            votes = meeting.events[meeting.motion_index + 1 :]  # type: ignore[operator]  # index is safe if vote is in progress
            in_favor = [event.message.sender for event in votes if event.operand == VotingAction.IN_FAVOR]
            opposed = [event.message.sender for event in votes if event.operand == VotingAction.OPPOSED]
            if not in_favor and not opposed:
                context.send_reply("Motion cannot be closed: no votes found (maybe use #inconclusive?)")
            else:
                meeting.vote_in_progress = False
                meeting.motion_index = None
                if len(in_favor) > len(opposed):
                    result = f"Motion accepted: {len(in_favor)} in favor to {len(opposed)} opposed"
                    meeting.track_event(EventType.ACCEPTED, message, operand=result)
                    context.send_reply(result)
                elif len(in_favor) < len(opposed):
                    result = f"Motion failed: {len(in_favor)} in favor to {len(opposed)} opposed"
                    meeting.track_event(EventType.FAILED, message, operand=result)
                    context.send_reply(result)
                elif len(in_favor) == len(opposed):
                    result = f"Motion inconclusive: {len(in_favor)} in favor to {len(opposed)} opposed"
                    meeting.track_event(EventType.INCONCLUSIVE, message, operand=result)
                    context.send_reply(result)
                context.send_reply(f"In favor: {', '.join(in_favor)}")
                context.send_reply(f"Opposed: {', '.join(opposed)}")

    def do_accepted(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has been accepted."""
        if meeting.is_chair(message.sender):
            meeting.vote_in_progress = False
            meeting.motion_index = None
            meeting.track_event(EventType.ACCEPTED, message, operand=operand)

    def do_failed(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion has failed."""
        if meeting.is_chair(message.sender):
            meeting.vote_in_progress = False
            meeting.motion_index = None
            meeting.track_event(EventType.FAILED, message, operand=operand)

    def do_inconclusive(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Indicate that a motion was inconclusive."""
        if meeting.is_chair(message.sender):
            meeting.vote_in_progress = False
            meeting.motion_index = None
            meeting.track_event(EventType.INCONCLUSIVE, message, operand=operand)

    def do_action(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an action item to the minutes."""
        meeting.track_event(EventType.ACTION, message, operand=operand)

    def do_info(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an informational item to the minutes."""
        meeting.track_event(EventType.INFO, message, operand=operand)

    def do_idea(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add an idea item to the minutes."""
        meeting.track_event(EventType.IDEA, message, operand=operand)

    def do_help(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a help item to the minutes."""
        meeting.track_event(EventType.HELP, message, operand=operand)

    def do_link(self, meeting: Meeting, context: Context, operation: str, operand: str, message: TrackedMessage) -> None:
        """Add a link to the minutes."""
        meeting.track_event(EventType.LINK, message, operand=operand)

    def _formatdate(self, timestamp: datetime | None) -> str:
        """Format a date in the user's configured time zone."""
        return formatdate(timestamp=timestamp, zone=config().timezone)

    def _tokenize(self, value: str, pattern: str = r"[\s,]+", limit: int | None = None) -> list[str]:
        """Tokenize a value, splitting via a regular expression and returning all non-empty values up to a limit."""
        if not value or not pattern:
            return []
        return [token.strip() for token in re.split(pattern, value) if token.strip()][:limit]

    def _set_channel_topic(self, meeting: Meeting, context: Context) -> None:
        """Set the channel topic based on the current state of the meeting."""

        # Attempting to set the topic will sometimes result in an error message like this
        # in the Limnoria logs:
        #
        #   Unhandled error message from server: IrcMsg(server_tags={}, prefix="sodium.libera.chat",
        #       command="482", args=('mybot', '#mychannel', "You're not a channel operator"))
        #
        # As far as I can tell, there's nothing we can do about this.  There does not seem
        # to be a way to detect whether the bot is a channel operator prior to issuing the
        # set topic command.  So, if a user knows that the bot won't be able to set the
        # topic, then they can explicitly configure config.use_channel_topic=False, and we
        # won't try to set it.

        if config().use_channel_topic:
            if meeting.active:
                if meeting.current_topic:
                    context.set_topic(f"{meeting.current_topic}")
                else:
                    context.set_topic("Meeting Active")
            else:
                context.set_topic(meeting.original_topic or "")


# Singleton command dispatcher
_DISPATCHER = CommandDispatcher()


def list_commands() -> list[str]:
    """List available commands."""
    return _DISPATCHER.list_commands()


def dispatch(meeting: Meeting, context: Context, message: TrackedMessage) -> None:
    """Dispatch any command contained in the message to the dispatcher method with the matching name."""
    if message.payload.lower().strip().startswith(meeting.channel.lower()):
        return
    operation_match = _OPERATION_REGEX.match(message.payload)
    url_match = _URL_REGEX.match(message.payload)
    if operation_match:
        operation = operation_match.group(_OPERATION_GROUP).lower().strip()
        operand = operation_match.group(_OPERAND_GROUP).strip()
        if hasattr(_DISPATCHER, f"{_METHOD_PREFIX}{operation}"):
            getattr(_DISPATCHER, f"{_METHOD_PREFIX}{operation}")(meeting, context, operation, operand, message)
        else:
            context.send_reply(f"Unknown command: #{operation}")
    elif url_match:
        # as a special case, turns messages that start with a URL into a link operation
        operation = "link"
        operand = url_match.group(_URL_GROUP)
        _DISPATCHER.do_link(meeting, context, operation, operand, message)


def is_startmeeting(message: Message) -> bool:
    """Whether the message contains a start-of-meeting indicator."""
    return bool(message.payload and _STARTMEETING_REGEX.match(message.payload))
