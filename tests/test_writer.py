# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=no-self-use,protected-access
from unittest.mock import MagicMock, patch

from hcoopmeetbotlogic.writer import write_meeting


class TestFunctions:
    @patch("hcoopmeetbotlogic.writer.derive_locations")
    def test_write_meeting(self, derive_locations):
        # TODO: expand this after implementing the function
        locations = MagicMock()
        derive_locations.return_value = locations
        config = MagicMock()
        meeting = MagicMock()
        assert write_meeting(config, meeting) is locations
        derive_locations.assert_called_once_with(config, meeting)
