# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Location logic.
"""
import os
import re
from pathlib import Path
from typing import Optional

import attr

from .config import Config, OutputFormat
from .dateutil import formatdate
from .meeting import Meeting

RAW_LOG_EXTENSION = ".log.json"
HTML_LOG_EXTENSION = ".log.html"
HTML_MINUTES_EXTENSION = ".html"


@attr.s(frozen=True)
class Location:
    """Path and URL for some persisted data."""

    path = attr.ib(type=str)
    url = attr.ib(type=str)


@attr.s(frozen=True)
class Locations:
    """Locations where meeting results were written."""

    raw_log = attr.ib(type=Location)
    formatted_log = attr.ib(type=Location)
    formatted_minutes = attr.ib(type=Location)


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


def derive_prefix(raw_log_path: str) -> str:
    """Derive the prefix associated with a raw log path, for use when regenerating output."""
    return os.path.basename(raw_log_path).removesuffix(RAW_LOG_EXTENSION)


def derive_locations(config: Config, meeting: Meeting, prefix: Optional[str] = None) -> Locations:
    """Derive the locations where meeting files will be written."""
    file_prefix = prefix if prefix else _file_prefix(config, meeting)
    if config.output_format == OutputFormat.HTML:
        return Locations(
            raw_log=_location(config, file_prefix, RAW_LOG_EXTENSION),
            formatted_log=_location(config, file_prefix, HTML_LOG_EXTENSION),
            formatted_minutes=_location(config, file_prefix, HTML_MINUTES_EXTENSION),
        )
    else:
        raise ValueError("Unsupported output format: %s" % config.output_format)
