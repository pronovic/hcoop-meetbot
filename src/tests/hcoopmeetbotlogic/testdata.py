# vim: set ft=python ts=4 sw=4 expandtab:

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from hcoopmeetbotlogic.interface import Message
from hcoopmeetbotlogic.meeting import EventType, Meeting, VotingAction

START_TIME = datetime(2021, 4, 13, 2, 6, 12, tzinfo=UTC)


def contents(path: str) -> str:
    """Get contents of a file for comparison."""
    return Path(path).read_text(encoding="utf-8")


def time(seconds: int) -> datetime:
    """Generate a timestamp relative to START_TIME"""
    return START_TIME + timedelta(seconds=seconds)


def message(identifier: int, nick: str, payload: str, seconds: int) -> Message:
    """Generate a mocked message with some values"""
    return MagicMock(id=f"id-{identifier}", nick=nick, payload=payload, timestamp=time(seconds))


def sample_meeting() -> Meeting:
    """Generate a semi-realistic meeting that can be used for unit tests"""

    # Initialize the meeting
    meeting = Meeting(founder="pronovic", channel="#hcoop", network="network")

    # this gets us some data in the attendees section without having to add tons of messages
    meeting.track_nick("unknown_lamer", 13)
    meeting.track_nick("layline", 32)
    meeting.track_nick("bhkl", 3)

    # Start the meeting
    meeting.active = True
    meeting.start_time = time(0)
    tracked = meeting.track_message(message=message(0, "pronovic", "#startmeeting", 0))
    meeting.track_event(event_type=EventType.START_MEETING, message=tracked)

    # these messages and events will be associated with the prologue, because no topic has been set yet
    tracked = meeting.track_message(message=message(1, "pronovic", "Hello everyone, is it ok to get started?", 32))
    tracked = meeting.track_message(message=message(2, "unknown_lamer", "Yeah, let's do it", 97))
    tracked = meeting.track_message(message=message(3, "pronovic", "#link Agenda at https://whatever/agenda.html like usual", 123))
    meeting.track_event(event_type=EventType.LINK, message=tracked, operand="Agenda at https://whatever/agenda.html like usual")

    # these messages and events are associated with the attendance topic
    # note that we track attendees manually since that's what would be done by the command interpreter
    tracked = meeting.track_message(message=message(4, "pronovic", "#topic Attendance", 125))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="Attendance")
    tracked = meeting.track_message(message=message(5, "pronovic", 'If you are present please write "#here $hcoop_username"', 126))
    tracked = meeting.track_message(message=message(6, "pronovic", "#here Pronovici", 127))  # note: alias != nick
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="Pronovici")
    meeting.track_attendee(nick="pronovic", alias="Pronovici")
    tracked = meeting.track_message(message=message(7, "unknown_lamer", "#here Clinton Alias", 128))  # note: alias != nick
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="Clinton Alias")
    meeting.track_attendee(nick="unknown_lamer", alias="Clinton Alias")
    tracked = meeting.track_message(message=message(8, "keverets", "#here keverets", 129))  # note: alias == nick
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="keverets")
    meeting.track_attendee(nick="keverets", alias="keverets")
    tracked = meeting.track_message(message=message(9, "layline", "#here", 130))  # note: no alias, so it's set to nick
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="layline")
    meeting.track_attendee(nick="layline", alias="layline")
    tracked = meeting.track_message(message=message(10, "pronovic", "Thanks, everyone", 130))

    # these messages and events are associated with the first topic
    tracked = meeting.track_message(message=message(11, "pronovic", "#topic The first topic", 199))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The first topic")
    tracked = meeting.track_message(message=message(12, "pronovic", "Does anyone have any discussion?", 231))
    tracked = meeting.track_message(message=message(13, "layline", "Is this important?", 232))
    tracked = meeting.track_message(message=message(14, "unknown_lamer", "Yes it is", 299))
    tracked = meeting.track_message(message=message(15, "pronovic", "#info moving on then", 305))
    meeting.track_event(event_type=EventType.INFO, message=tracked, operand="moving on then")

    # these messages and events are associated with the second topic
    tracked = meeting.track_message(message=message(16, "pronovic", "#topic The second topic", 332))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The second topic")
    tracked = meeting.track_message(message=message(17, "layline", "\x01unknown_lamer: I need you for this action\x01", 334))
    tracked = meeting.track_message(message=message(18, "pronovic", "#action clinton alias will work with layline on this", 401))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="clinton alias will work with layline on this")

    # these messages and events are associated with the third topic
    tracked = meeting.track_message(message=message(19, "pronovic", "#topic The third topic", 407))
    meeting.track_event(event_type=EventType.TOPIC, message=tracked, operand="The third topic")
    tracked = meeting.track_message(message=message(20, "pronovic", "#idea we should improve MeetBot", 414))
    meeting.track_event(event_type=EventType.IDEA, message=tracked, operand="we should improve MeetBot")
    tracked = meeting.track_message(message=message(21, "pronovic", "I'll just take this one myself", 435))
    tracked = meeting.track_message(message=message(22, "pronovic", "#action pronovici will deal with it", 449))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="pronovici will deal with it")

    # these messages and events are associated with the final topic
    tracked = meeting.track_message(message=message(23, "pronovic", "#topic Cross-site Scripting", 453))
    tracked = meeting.track_message(message=message(24, "pronovic", "#action <script>alert('malicious')</script>", 497))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="<script>alert('malicious')</script>")
    tracked = meeting.track_message(message=message(25, "pronovic", "#motion the motion", 502))
    meeting.track_event(event_type=EventType.MOTION, message=tracked, operand="the motion")
    tracked = meeting.track_message(message=message(26, "pronovic", "#vote +1", 553))
    meeting.track_event(event_type=EventType.VOTE, message=tracked, operand=VotingAction.IN_FAVOR)
    tracked = meeting.track_message(message=message(27, "unknown_lamer", "#vote +1", 555))
    meeting.track_event(event_type=EventType.VOTE, message=tracked, operand=VotingAction.IN_FAVOR)
    tracked = meeting.track_message(message=message(28, "layline", "#vote -1", 557))
    meeting.track_event(event_type=EventType.VOTE, message=tracked, operand=VotingAction.OPPOSED)
    tracked = meeting.track_message(message=message(29, "pronovic", "#close", 559))
    meeting.track_event(event_type=EventType.ACCEPTED, message=tracked, operand="Motion accepted: 2 in favor to 1 opposed")

    tracked = meeting.track_message(message=message(30, "pronovic", "#nick k[n", 560))
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="k[n")
    tracked = meeting.track_message(message=message(31, "unknown_lamer", "#action hey k[n, your nick has special chars", 561))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="hey k[n, your nick has regex special characters")
    tracked = meeting.track_message(message=message(32, "ken[", "#here", 562))
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="ke[")
    meeting.track_attendee(nick="ken[", alias="ken[")
    tracked = meeting.track_message(message=message(33, "layline", "#action ken] fix your nick!", 563))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="ken] fix your nick!")
    tracked = meeting.track_message(message=message(34, "[ken", "#here", 564))
    meeting.track_event(event_type=EventType.ATTENDEE, message=tracked, operand="[ken")
    meeting.track_attendee(nick="[ken", alias="[ken")
    tracked = meeting.track_message(message=message(35, "pronovic", "#action not you too, [ken", 565))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="not you too, [ken")
    tracked = meeting.track_message(message=message(36, "[m]", "#here", 566))
    meeting.track_attendee(nick="[m]", alias="[m]")
    tracked = meeting.track_message(message=message(37, "keverets", "#action A Matrix [m] nick", 567))
    meeting.track_event(event_type=EventType.ACTION, message=tracked, operand="A Matrix [m] nick")

    # End the meeting
    tracked = meeting.track_message(message=message(38, "pronovic", "#endmeeting", 570))
    meeting.track_event(event_type=EventType.END_MEETING, message=tracked)
    meeting.active = False
    meeting.end_time = time(570)

    return meeting
