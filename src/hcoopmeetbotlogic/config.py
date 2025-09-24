# vim: set ft=python ts=4 sw=4 expandtab:

"""
Plugin configuration and parsing.
"""

import configparser
from enum import StrEnum
from logging import Logger
from pathlib import Path

from attrs import frozen

CONF_FILE = "HcoopMeetbot.conf"
CONF_SECTION = "HcoopMeetbot"

LOG_DIR_KEY = "logDir"
URL_PREFIX_KEY = "urlPrefix"
PATTERN_KEY = "pattern"
TIMEZONE_KEY = "timezone"
USE_CHANNEL_TOPIC_KEY = "useChannelTopic"
OUTPUT_FORMAT_KEY = "outputFormat"

LOG_DIR_DEFAULT = str(Path.home() / "hcoop-meetbot")
URL_PREFIX_DEFAULT = "/"
PATTERN_DEFAULT = "%Y/{name}.%Y%m%d.%H%M"
TIMEZONE_DEFAULT = "UTC"
USE_CHANNEL_TOPIC_DEFAULT = False


class OutputFormat(StrEnum):
    """Legal output formats."""

    HTML = "HTML"


OUTPUT_FORMAT_DEFAULT = OutputFormat.HTML


@frozen
class Config:
    # noinspection PyUnresolvedReferences
    """
    Configuration for the plugin.

    Attributes:
        conf_file(Optional[str]): Path to the file where configuration was sourced from
        log_dir(str): Absolute path where meeting logs will be written
        url_prefix(str): URL prefix to place on generated links to logfiles
        pattern(str): Pattern for files generated in logFileDir
        timezone(str): Timezone string, any value valid for pytz
        use_channel_topic(bool): Whether the bot should attempt to use the channel topic
        output_format(OutputFormat): The output format to use
    """

    conf_file: str | None
    log_dir: str = LOG_DIR_DEFAULT
    url_prefix: str = URL_PREFIX_DEFAULT
    pattern: str = PATTERN_DEFAULT
    timezone: str = TIMEZONE_DEFAULT
    use_channel_topic: bool = USE_CHANNEL_TOPIC_DEFAULT
    output_format: OutputFormat = OUTPUT_FORMAT_DEFAULT


def load_config(logger: Logger | None, conf_path: str) -> Config:
    """
    Load configuration from disk.

    If conf_path is a directory, then HcoopMeetbot.conf will be loaded from
    that directory.  If conf_path is a file, then that file will be loaded
    instead.  If the entire file doesn't exist, defaults will be used for
    all fields.

    The configuration on disk may contain any or all of the configuration fields.
    A default (fallback) value will be used for any field that does not exist.

    Args:
        logger(Logger): Python logger instance that should be used during processing
        conf_path(str): Limnoria bot config path to load configuration from, either a file or a directory
    """

    def parse_config(source: str) -> Config:
        if not Path(source).is_file():
            if logger:
                logger.debug("Could not find %s; using defaults", source)
            return Config(conf_file=None)
        try:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read([source], encoding="utf-8")
            return Config(
                conf_file=source,
                log_dir=parser.get(CONF_SECTION, LOG_DIR_KEY, fallback=LOG_DIR_DEFAULT),
                url_prefix=parser.get(CONF_SECTION, URL_PREFIX_KEY, fallback=URL_PREFIX_DEFAULT),
                pattern=parser.get(CONF_SECTION, PATTERN_KEY, fallback=PATTERN_DEFAULT),
                timezone=parser.get(CONF_SECTION, TIMEZONE_KEY, fallback=TIMEZONE_DEFAULT),
                use_channel_topic=parser.getboolean(CONF_SECTION, USE_CHANNEL_TOPIC_KEY, fallback=USE_CHANNEL_TOPIC_DEFAULT),
                output_format=OutputFormat[
                    parser.get(CONF_SECTION, OUTPUT_FORMAT_KEY, fallback=OUTPUT_FORMAT_DEFAULT.name).upper()
                ],
            )
        except Exception:
            if logger:
                logger.exception("Failed to parse %s; using defaults", source)
            return Config(conf_file=None)

    conf_file = Path(conf_path) / CONF_FILE if Path(conf_path).is_dir() else Path(conf_path)
    config = parse_config(str(conf_file))
    if logger:
        logger.info("HcoopMeetbot config: %s", config)
    return config
