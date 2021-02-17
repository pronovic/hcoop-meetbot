# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
IRC request and message handlers.
"""

import configparser
import os
from logging import Logger
from pathlib import Path

from .interface import Config, Context, Message
from .release import DATE, VERSION

CONF_FILE = "HcoopMeetbot.conf"
CONF_SECTION = "HcoopMeetbot"

CONF_LOG_DIR_KEY = "logDir"
CONF_URL_PREFIX_KEY = "urlPrefix"
CONF_PATTERN_KEY = "pattern"
CONF_TIMEZONE_KEY = "timezone"

CONF_LOG_DIR_DEFAULT = os.path.join(Path.home(), "hcoop-meetbot")
CONF_URL_PREFIX_DEFAULT = ""
CONF_PATTERN_DEFAULT = "%%Y/%(channel)s.%%Y%%m%%d.%%H%%M"
CONF_TIMEZONE_DEFAULT = "UTC"

_LOGGER: Logger
_CONFIG: Config


def _logger() -> Logger:
    """Give unit tests access"""
    return _LOGGER  # for some reason, global doesn't do what we expect


def _config() -> Config:
    """Give unit tests access"""
    return _CONFIG  # for some reason, global doesn't do what we expect


def configure(logger: Logger, conf_dir: str) -> None:
    """
    Configure the plugin.

    Args:
        logger(Logger): Python logger instance that should be used during processing
        conf_dir(str): Limnoria bot conf directory to load configuration from
    """
    global _LOGGER  # pylint: disable=global-statement:
    global _CONFIG  # pylint: disable=global-statement:
    _LOGGER = logger
    _CONFIG = None  # type: ignore
    conf_file = os.path.join(conf_dir, CONF_FILE)
    if os.path.isfile(conf_file):
        try:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read([conf_file], encoding="utf-8")
            _CONFIG = Config(
                conf_file=conf_file,
                log_dir=parser[CONF_SECTION][CONF_LOG_DIR_KEY],
                url_prefix=parser[CONF_SECTION][CONF_URL_PREFIX_KEY],
                pattern=parser[CONF_SECTION][CONF_PATTERN_KEY],
                timezone=parser[CONF_SECTION][CONF_TIMEZONE_KEY],
            )
        except Exception:  # pylint: disable=broad-except:
            _LOGGER.exception("Failed to parse %s; using defaults", conf_file)
    if not _CONFIG:
        _CONFIG = Config(
            conf_file=None,
            log_dir=CONF_LOG_DIR_DEFAULT,
            url_prefix=CONF_URL_PREFIX_DEFAULT,
            pattern=CONF_PATTERN_DEFAULT,
            timezone=CONF_TIMEZONE_DEFAULT,
        )
    _LOGGER.info("HcoopMeetbot config: %s", _CONFIG)


def irc_message(context: Context, message: Message) -> None:  # pylint: disable=unused-argument:
    """
    Handle an IRC message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    _LOGGER.info("Received message: %s", message)


def outbound_message(context: Context, message: Message) -> None:  # pylint: disable=unused-argument:
    """
    Handle an outbound message from the bot.

    Args:
        context(Context): Context for the message
        message(Message): Message to handle
    """
    _LOGGER.info("Received message: %s", message)


def meetversion(context: Context) -> None:  # pylint: disable=unused-argument:
    """Reply with a string describing the version of the plugin."""
    context.send_reply("HcoopMeetbot v%s, released %s" % (VERSION, DATE))


def listmeetings(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    List all currently-active meetings.

    Args:
        context(Context): Context for a message or command
    """
    _LOGGER.info("Handled listmeetings")


def savemeetings(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    Save all currently active meetings.

    Args:
        context(Context): Context for a message or command
    """
    _LOGGER.info("Handled savemeetings")


def addchair(context: Context, channel: str, network: str, nick: str) -> None:  # pylint: disable=unused-argument:
    """
    Add a nickname as a chair to the meeting.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to add the chair for
        network(str): Network to add the chair for
        nick(str): Nickname to add as the chair
    """
    _LOGGER.info("Handled addchair for [%s] [%s] [%s]", channel, network, nick)


def deletemeeting(context: Context, channel: str, network: str, save: bool) -> None:  # pylint: disable=unused-argument:
    """
    Delete a meeting from the cache.

    Args:
        context(Context): Context for a message or command
        channel(str): Channel to delete the meeting for
        network(str): Network to delete the meeting for
        save(bool): Whether to save the meeting before deleting it
    """
    _LOGGER.info("Handled deletemeeting for [%s] [%s] [%s]", channel, network, save)


def recent(context: Context) -> None:  # pylint: disable=unused-argument:
    """
    List recent meetings for admin purposes."

    Args:
        context(Context): Context for a message or command
    """
    _LOGGER.info("Handled recent")
