# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import os
from datetime import datetime
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from hcoopmeetbotlogic.location import Location, Locations
from hcoopmeetbotlogic.meeting import TrackedMessage
from hcoopmeetbotlogic.writer import write_meeting

EXPECTED_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/log.expected")
EXPECTED_MINUTES = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/minutes.expected")


def _contents(path: str) -> str:
    """Get contents of a file for comparison."""
    with open(path, "r") as out:
        return out.read()


class TestRendering:
    @patch("hcoopmeetbotlogic.writer.derive_locations")
    def test_write_meeting_wiring(self, derive_locations):
        # The goal here is to prove that rendering is wired up properly and that
        # files are written as expected.  We don't verify every different rendering
        # scenario - there are other tests that are intended to test the underlying
        # implementation at that level of detail.
        with TemporaryDirectory() as temp:
            log = Location(path=os.path.join(temp, "log.expected"), url="http://")
            minutes = Location(path=os.path.join(temp, "minutes.expected"), url="http://")
            locations = Locations(log=log, minutes=minutes)
            derive_locations.return_value = locations
            config = MagicMock(timezone="UTC")
            meeting = MagicMock()
            meeting.name = "#hcoop"
            meeting.messages = [
                TrackedMessage(id="id1", action=False, sender="nick1", timestamp=datetime(2021, 3, 7, 13, 14, 0), payload="stuff")
            ]
            assert write_meeting(config, meeting) is locations
            derive_locations.assert_called_once_with(config, meeting)
            print(_contents(log.path))
            assert _contents(log.path) == _contents(EXPECTED_LOG)
            assert _contents(minutes.path) == _contents(EXPECTED_MINUTES)
