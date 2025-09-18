# vim: set ft=python ts=4 sw=4 expandtab:

"""
Version and release information.
"""

# Historically, this information was tracked directly within this file as part of the
# release process.  In modern Python, it's better to rely on the package metadata,
# which is managed by Poetry on our behalf.
#
# The metadata will always be set any time the package has been completely and
# properly installed, but defaults are provided for times when this is not the case.
#
# Note: previously, we also tracked release date (DATE) and copyright date range
# (COPYRIGHT), but that information is not available in the package metadata.  These
# variables are maintained to avoid breaking the public interface, but are always
# "unset".
#
# See also:
#   https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata-project-url
#   https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-project-urls

from importlib.metadata import PackageMetadata, metadata
from typing import cast

try:
    _METADATA = metadata("hcoop-meetbot")
except ImportError:
    _METADATA = cast("PackageMetadata", {})


def _metadata(key: str, default: str) -> str:
    return _METADATA[key] if key in _METADATA else default  # noqa


def _project_url(key: str, default: str) -> str:
    urls = _METADATA.get_all("Project-URL")
    if urls is None:
        urls = []
    return next(
        iter([url.replace(f"{key}, ", "") for url in urls if url.startswith(f"{key}, ")]),
        default,
    )


AUTHOR = _metadata("Author", "unset")
EMAIL = _metadata("Author-email", "unset")
VERSION = _metadata("Version", "0.0.0")
URL = _project_url("Homepage", "unset")
DOCS = _project_url("Documentation", "unset")

COPYRIGHT = "unset"
DATE = "unset"
