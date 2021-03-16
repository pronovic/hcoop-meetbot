# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Plugin configuration and parsing.
"""

import configparser
import os
from logging import Logger
from pathlib import Path
from typing import Optional

import attr

CONF_FILE = "HcoopMeetbot.conf"
CONF_SECTION = "HcoopMeetbot"

LOG_DIR_KEY = "logDir"
URL_PREFIX_KEY = "urlPrefix"
PATTERN_KEY = "pattern"
TIMEZONE_KEY = "timezone"

LOG_DIR_DEFAULT = os.path.join(Path.home(), "hcoop-meetbot")
URL_PREFIX_DEFAULT = "/"
PATTERN_DEFAULT = "%Y/{name}.%Y%m%d.%H%M"
TIMEZONE_DEFAULT = "UTC"


@attr.s(frozen=True)
class Config:
    """
    Configuration for the plugin.

    Attributes:
        conf_file(Optional[str]): Path to the file where configuration was sourced from
        log_dir(str): Absolute path where meeting logs will be written
        url_prefix(str): URL prefix to place on generated links to logfiles
        pattern(str): Pattern for files generated in logFileDir
        timezone(str): Timezone string, any value valid for pytz
    """

    conf_file = attr.ib(type=Optional[str])
    log_dir = attr.ib(type=str, default=LOG_DIR_DEFAULT)
    url_prefix = attr.ib(type=str, default=URL_PREFIX_DEFAULT)
    pattern = attr.ib(type=str, default=PATTERN_DEFAULT)
    timezone = attr.ib(type=str, default=TIMEZONE_DEFAULT)


def load_config(logger: Logger, conf_dir: str) -> Config:
    """
    Load configuration from disk.

    The configuration on disk may contain any or all of the configuration fields.
    A default (fallback) value will be used for any field that does not exist.
    If the entire file doesn't exist, defaults will be used for all fields.

    Args:
        logger(Logger): Python logger instance that should be used during processing
        conf_dir(str): Limnoria bot conf directory to load configuration from
    """
    config: Config
    conf_file = os.path.join(conf_dir, CONF_FILE)
    if os.path.isfile(conf_file):
        try:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read([conf_file], encoding="utf-8")
            config = Config(
                conf_file=conf_file,
                log_dir=parser.get(CONF_SECTION, LOG_DIR_KEY, fallback=LOG_DIR_DEFAULT),
                url_prefix=parser.get(CONF_SECTION, URL_PREFIX_KEY, fallback=URL_PREFIX_DEFAULT),
                pattern=parser.get(CONF_SECTION, PATTERN_KEY, fallback=PATTERN_DEFAULT),
                timezone=parser.get(CONF_SECTION, TIMEZONE_KEY, fallback=TIMEZONE_DEFAULT),
            )
        except Exception:  # pylint: disable=broad-except:
            logger.exception("Failed to parse %s; using defaults", conf_file)
            config = Config(conf_file=None)
    else:
        config = Config(conf_file=None)
    logger.info("HcoopMeetbot config: %s", config)
    return config
