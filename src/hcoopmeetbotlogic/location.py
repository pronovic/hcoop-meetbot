# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Location logic.
"""

import re
from pathlib import Path

import attr

from .config import Config
from .dateutil import formatdate
from .meeting import Meeting


@attr.s(frozen=True)
class Location:
    """Path and URL for some persisted data."""

    path = attr.ib(type=str)
    url = attr.ib(type=str)


@attr.s(frozen=True)
class Locations:
    """Locations where meeting results were written."""

    log = attr.ib(type=Location)
    minutes = attr.ib(type=Location)


def _file_prefix(config: Config, meeting: Meeting) -> str:
    """Build the file prefix used for generating meeting-related files."""
    fmt = re.sub(r"^/", "", config.pattern).format(**vars(meeting))  # Substitute in meeting fields
    prefix = formatdate(meeting.start_time, zone=config.timezone, fmt=fmt)  # Substitute in date fields
    normalized = re.sub(r"[#]+", "", prefix)  # We track channel name as "#channel" but we don't want it in path
    normalized = re.sub(r"[^./a-zA-Z0-9_-]+", "_", normalized)  # Normalize to a sane path without confusing characters
    return normalized


def _abs_path(config: Config, file_prefix: str, suffix: str) -> str:
    """Build an absolute path for a file in the log directory, preventing path traversal."""
    log_dir = Path(config.log_dir)
    target = "%s%s" % (file_prefix, suffix)  # might include slashes and other traversal like ".."
    safe = log_dir.joinpath(target).resolve().relative_to(log_dir.resolve())  # blows up if outside of log dir
    return log_dir.joinpath(safe).absolute().as_posix()


def _url(config: Config, file_prefix: str, suffix: str) -> str:
    """Build a URL for a file in the log directory."""
    # We don't worry about path traversal here, because it's up to the webserver to decide what is allowed
    return "%s/%s%s" % (config.url_prefix, file_prefix, suffix)


def _location(config: Config, file_prefix: str, suffix: str) -> Location:
    """Build a location for a file in the log directory"""
    path = _abs_path(config, file_prefix, suffix)
    url = _url(config, file_prefix, suffix)
    return Location(path=path, url=url)


def derive_locations(config: Config, meeting: Meeting) -> Locations:
    """Derive the locations where meeting files will be written."""
    file_prefix = _file_prefix(config, meeting)
    log = _location(config, file_prefix, ".log.html")
    minutes = _location(config, file_prefix, ".html")
    return Locations(log=log, minutes=minutes)
