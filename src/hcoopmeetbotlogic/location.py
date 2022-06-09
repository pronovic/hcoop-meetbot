# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Location logic.
"""
import os
import re
from pathlib import Path
from typing import Optional

from attrs import frozen

from .config import Config, OutputFormat
from .dateutil import formatdate
from .meeting import Meeting

RAW_LOG_EXTENSION = ".log.json"
HTML_LOG_EXTENSION = ".log.html"
HTML_MINUTES_EXTENSION = ".html"


@frozen
class Location:
    """Path and URL for some persisted data."""

    path: str
    url: str


@frozen
class Locations:
    """Locations where meeting results were written."""

    raw_log: Location
    formatted_log: Location
    formatted_minutes: Location


def _file_prefix(config: Config, meeting: Meeting) -> str:
    """Build the file prefix used for generating meeting-related files."""
    fmt = re.sub(r"^/", "", config.pattern).format(**vars(meeting))  # Substitute in meeting fields
    prefix = formatdate(meeting.start_time, zone=config.timezone, fmt=fmt)  # Substitute in date fields
    normalized = re.sub(r"[#]+", "", prefix)  # We track channel name as "#channel" but we don't want it in path
    normalized = re.sub(r"[^./a-zA-Z0-9_-]+", "_", normalized)  # Normalize to a sane path without confusing characters
    return normalized


def _abs_path(config: Config, file_prefix: str, suffix: str, output_dir: Optional[str]) -> str:
    """Build an absolute path for a file in the log directory, preventing path traversal."""
    log_dir = Path(output_dir) if output_dir else Path(config.log_dir)
    target = "%s%s" % (file_prefix, suffix)  # might include slashes and other traversal like ".."
    safe = log_dir.joinpath(target).resolve().relative_to(log_dir.resolve())  # blows up if outside of log dir
    return log_dir.joinpath(safe).absolute().as_posix()


def _url(config: Config, file_prefix: str, suffix: str) -> str:
    """Build a URL for a file in the log directory."""
    # We don't worry about path traversal here, because it's up to the webserver to decide what is allowed
    return "%s/%s%s" % (config.url_prefix, file_prefix, suffix)


def _location(config: Config, file_prefix: str, suffix: str, output_dir: Optional[str]) -> Location:
    """Build a location for a file in the log directory"""
    path = _abs_path(config, file_prefix, suffix, output_dir)
    url = _url(config, file_prefix, suffix)
    return Location(path=path, url=url)


def _removesuffix(content: str, suffix: str) -> str:
    # equivalent to string.removesuffix, which is only available in Python 3.9
    return content[: -len(suffix)] if content.endswith(suffix) else content


def derive_prefix(raw_log_path: str) -> str:
    """Derive the prefix associated with a raw log path, for use when regenerating output."""
    return _removesuffix(os.path.basename(raw_log_path), RAW_LOG_EXTENSION)


def derive_locations(config: Config, meeting: Meeting, prefix: Optional[str] = None, output_dir: Optional[str] = None) -> Locations:
    """
    Derive the locations where meeting files will be written.

    Use prefix and output_dir to override the file prefix and output log directory
    that would normally be generated based on configuration.
    """
    file_prefix = prefix if prefix else _file_prefix(config, meeting)
    if config.output_format == OutputFormat.HTML:
        return Locations(
            raw_log=_location(config, file_prefix, RAW_LOG_EXTENSION, output_dir),
            formatted_log=_location(config, file_prefix, HTML_LOG_EXTENSION, output_dir),
            formatted_minutes=_location(config, file_prefix, HTML_MINUTES_EXTENSION, output_dir),
        )
    else:
        raise ValueError("Unsupported output format: %s" % config.output_format)
