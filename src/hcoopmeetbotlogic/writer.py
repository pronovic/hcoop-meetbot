# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Writes meeting log and minutes to disk.
"""
import os
from typing import Any, Dict, TextIO

from genshi.template import MarkupTemplate, TemplateLoader

from hcoopmeetbotlogic.config import Config

from .location import Location, Locations, derive_locations
from .meeting import Meeting

_TEMPLATES = os.path.join(os.path.dirname(__file__), "templates")
_LOADER = TemplateLoader(search_path=_TEMPLATES, auto_reload=False)


def _render_html(template: str, context: Dict[str, Any], out: TextIO) -> None:
    """Render the named template to HTML, writing into the provided file."""
    renderer = _LOADER.load(filename=template, cls=MarkupTemplate)  # type: MarkupTemplate
    renderer.generate().render(method="html", doctype="html", out=out, **context)


# TODO: remove unused-argument
def _write_log(location: Location, meeting: Meeting) -> None:  # pylint: disable=unused-argument:
    """Write the meeting log to disk."""
    with open(location.path, "x") as out:
        _render_html(template="log.html", context={}, out=out)


# TODO: remove unused-argument
def _write_minutes(location: Location, meeting: Meeting) -> None:  # pylint: disable=unused-argument:
    """Write the meeting minutes to disk."""
    with open(location.path, "x") as out:
        _render_html(template="minutes.html", context={}, out=out)


def write_meeting(config: Config, meeting: Meeting) -> Locations:
    """Write meeting files to disk, returning the file locations."""
    locations = derive_locations(config, meeting)
    _write_log(location=locations.log, meeting=meeting)
    _write_minutes(location=locations.minutes, meeting=meeting)
    return locations
