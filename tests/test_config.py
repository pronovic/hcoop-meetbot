# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=protected-access
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hcoopmeetbotlogic.config import Config, OutputFormat, load_config

MISSING_DIR = "bogus"
VALID_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/valid")  # valid config with no optional values
OPTIONAL_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/optional")  # valid config with optional values
NO_CHANNEL_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/nochannel")
NO_FILE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/nofile")
EMPTY_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/empty")
INVALID_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/invalid")
BAD_BOOLEAN_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/bad_boolean")
BAD_FORMAT_DIR = os.path.join(os.path.dirname(__file__), "fixtures/test_config/bad_format")


@pytest.fixture
def context():
    stub = MagicMock()
    stub.send_reply = MagicMock()
    return stub


class TestConfig:
    def test_constructor(self):
        config = Config("conf_file", "log_dir", "url_prefix", "pattern", "timezone", True, OutputFormat.HTML)
        assert config.conf_file == "conf_file"
        assert config.log_dir == "log_dir"
        assert config.url_prefix == "url_prefix"
        assert config.pattern == "pattern"
        assert config.timezone == "timezone"
        assert config.use_channel_topic is True
        assert config.output_format == OutputFormat.HTML


class TestParsing:
    def test_valid_configuration_dir(self):
        logger = MagicMock()
        conf_dir = VALID_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")  # if the caller provides a directory, we always load this file
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)
        assert config.conf_file == conf_file
        assert config.log_dir == "/tmp/meetings"
        assert config.url_prefix == "https://whatever/meetings"
        assert config.pattern == "{name}-%Y%m%d"
        assert config.timezone == "America/Chicago"
        assert config.use_channel_topic is True
        assert config.output_format == OutputFormat.HTML

    def test_valid_configuration_file(self):
        logger = MagicMock()
        conf_dir = VALID_DIR
        conf_file = os.path.join(conf_dir, "CustomName.conf")  # for anything other than a directory, we open it like a file
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_file)
        assert config.conf_file == conf_file
        assert config.log_dir == "/tmp/custom"
        assert config.url_prefix == "https://whatever/custom"
        assert config.pattern == "{name}-%Y%m%d"
        assert config.timezone == "America/Chicago"
        assert config.use_channel_topic is True
        assert config.output_format == OutputFormat.HTML

    def test_valid_configuration_with_optional(self):
        logger = MagicMock()
        conf_dir = OPTIONAL_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)
        assert config.conf_file == conf_file
        assert config.log_dir == "/tmp/meetings"
        assert config.url_prefix == "https://whatever/meetings"
        assert config.pattern == "{name}-%Y%m%d"
        assert config.timezone == "America/Chicago"
        assert config.use_channel_topic is True
        assert config.output_format == OutputFormat.HTML

    def test_no_channel_configuration(self):
        logger = MagicMock()
        conf_dir = NO_CHANNEL_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)
        assert config.conf_file == conf_file
        assert config.log_dir == "/tmp/meetings"
        assert config.url_prefix == "https://whatever/meetings"
        assert config.pattern == "{name}-%Y%m%d"
        assert config.timezone == "America/Chicago"
        assert config.use_channel_topic is False

    def test_empty_configuration(self):
        logger = MagicMock()
        conf_dir = EMPTY_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)  # any key that can't be loaded gets defaults
        assert config.conf_file == conf_file
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"
        assert config.use_channel_topic is False

    def test_bad_boolean_configuration(self):
        logger = MagicMock()
        conf_dir = BAD_BOOLEAN_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)  # since the boolean value is invalid, it's like the file doesn't exist
        assert config.conf_file is None
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"
        assert config.use_channel_topic is False

    def test_bad_format_configuration(self):
        logger = MagicMock()
        conf_dir = BAD_FORMAT_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)  # since the output format is invalid, it's like the file doesn't exist
        assert config.conf_file is None
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"
        assert config.use_channel_topic is False

    def test_invalid_configuration(self):
        logger = MagicMock()
        conf_dir = INVALID_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.isdir(conf_dir) and os.path.isfile(conf_file)
        config = load_config(logger, conf_dir)  # since the file is invalid, it's like the keys don't exist
        assert config.conf_file == conf_file
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"
        assert config.use_channel_topic is False

    def test_missing_configuration_dir(self):
        logger = MagicMock()
        conf_dir = MISSING_DIR
        assert not os.path.exists(conf_dir)
        config = load_config(logger, conf_dir)  # if the directory does not exist, we use defaults
        assert config.conf_file is None
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"

    def test_missing_configuration_file_default(self):
        logger = MagicMock()
        conf_dir = NO_FILE_DIR
        conf_file = os.path.join(conf_dir, "HcoopMeetbot.conf")
        assert os.path.exists(conf_dir) and not os.path.exists(conf_file)
        config = load_config(logger, conf_dir)  # if the directory exists, but the file does not exist within, we use defaults
        assert config.conf_file is None
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"

    def test_missing_configuration_file_custom(self):
        logger = MagicMock()
        conf_dir = NO_FILE_DIR
        conf_file = os.path.join(conf_dir, "AnyFile.conf")
        assert os.path.exists(conf_dir) and not os.path.exists(conf_file)
        config = load_config(logger, conf_file)  # if the directory exists, but the file does not exist within, we use defaults
        assert config.conf_file is None
        assert config.log_dir == os.path.join(Path.home(), "hcoop-meetbot")
        assert config.url_prefix == "/"
        assert config.pattern == "%Y/{name}.%Y%m%d.%H%M"
        assert config.timezone == "UTC"
