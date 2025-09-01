# vim: set ft=python ts=4 sw=4 expandtab:

"""
Location logic.
"""

import re
from pathlib import Path

from attrs import frozen

from hcoopmeetbotlogic.config import Config, OutputFormat
from hcoopmeetbotlogic.dateutil import formatdate
from hcoopmeetbotlogic.meeting import Meeting

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
    return re.sub(r"[^./a-zA-Z0-9_-]+", "_", normalized)  # Normalize to a sane path without confusing characters


def _abs_path(config: Config, file_prefix: str, suffix: str, output_dir: str | None) -> str:
    """Build an absolute path for a file in the log directory, preventing path traversal."""
    log_dir = Path(output_dir) if output_dir else Path(config.log_dir)
    target = f"{file_prefix}{suffix}"  # might include slashes and other traversal like ".."
    safe = log_dir.joinpath(target).resolve().relative_to(log_dir.resolve())  # blows up if outside of log dir
    return log_dir.joinpath(safe).absolute().as_posix()


def _url(config: Config, file_prefix: str, suffix: str) -> str:
    """Build a URL for a file in the log directory."""
    # We don't worry about path traversal here, because it's up to the webserver to decide what is allowed
    return f"{config.url_prefix}/{file_prefix}{suffix}"


def _location(config: Config, file_prefix: str, suffix: str, output_dir: str | None) -> Location:
    """Build a location for a file in the log directory"""
    path = _abs_path(config, file_prefix, suffix, output_dir)
    url = _url(config, file_prefix, suffix)
    return Location(path=path, url=url)


def _removesuffix(content: str, suffix: str) -> str:
    # equivalent to string.removesuffix, which is only available in Python 3.9
    return content.removesuffix(suffix)


def derive_prefix(raw_log_path: str) -> str:
    """Derive the prefix associated with a raw log path, for use when regenerating output."""
    return _removesuffix(Path(raw_log_path).name, RAW_LOG_EXTENSION)


# noinspection PyUnreachableCode
def derive_locations(config: Config, meeting: Meeting, prefix: str | None = None, output_dir: str | None = None) -> Locations:
    """
    Derive the locations where meeting files will be written.

    Use prefix and output_dir to override the file prefix and output log directory
    that would normally be generated based on configuration.
    """
    file_prefix = prefix or _file_prefix(config, meeting)
    if config.output_format == OutputFormat.HTML:
        return Locations(
            raw_log=_location(config, file_prefix, RAW_LOG_EXTENSION, output_dir),
            formatted_log=_location(config, file_prefix, HTML_LOG_EXTENSION, output_dir),
            formatted_minutes=_location(config, file_prefix, HTML_MINUTES_EXTENSION, output_dir),
        )
    raise ValueError(f"Unsupported output format: {config.output_format}")
