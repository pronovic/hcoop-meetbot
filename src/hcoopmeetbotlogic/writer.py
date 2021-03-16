# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Writes meeting log and minutes to disk.
"""
from hcoopmeetbotlogic.config import Config

from .location import Locations, derive_locations
from .meeting import Meeting


def write_meeting(config: Config, meeting: Meeting) -> Locations:
    """Write meeting files to disk, returning the file locations."""
    # TODO: implement the real file save behavior
    return derive_locations(config, meeting)
