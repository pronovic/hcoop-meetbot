# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Meeting writers.
"""

from hcoopmeetbotlogic.meeting import Meeting

from .config import Config


# TODO: remove pylint disable statement once method is implemented
def write_meeting(config: Config, meeting: Meeting) -> None:  # pylint: disable=unused-argument:
    """Write a meeting to disk."""
    # TODO: implement code to write results to disk, HTML format only to start with
