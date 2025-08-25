# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
import sys
from tempfile import TemporaryDirectory
from typing import List
from unittest.mock import ANY, MagicMock, patch

import pytest
from click.testing import CliRunner, Result

from hcoopmeetbotlogic.cli import meetbot as command
from hcoopmeetbotlogic.config import OutputFormat
from hcoopmeetbotlogic.location import Location, Locations

from .testdata import contents

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "fixtures/test_config/valid/HcoopMeetbot.conf")
RAW_LOG_PREFIX = "2022-06-04"
RAW_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_cli/%s.log.json" % RAW_LOG_PREFIX)
EXPECTED_LOG = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/log.html")
EXPECTED_MINUTES = os.path.join(os.path.dirname(__file__), "fixtures/test_writer/minutes.html")


# noinspection PyTypeChecker
def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(command, args)


class TestCommon:
    def test_h(self):
        result = invoke(["-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["--help"])
        assert result.exit_code == 0

    @pytest.mark.skipif(sys.version_info >= (3, 9), reason="see comments")
    def test_version(self):
        # This tests the --version switch, without fully verifying its output.  This test should
        # succeed on all versions of Python that we support, including older versions that rely
        # on the importlib-metadata backport package.
        result = invoke(["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("hcoop-meetbot, version")

    @patch("importlib.metadata.version")  # this is used underneath by @click.version_option()
    @pytest.mark.skipif(sys.version_info < (3, 9), reason="see comments")
    def test_version_output(self, version):
        # This tests the --version switch, and fully verifies its output.  It will only succeed on
        # Python >= 3.9, where importlib.metadata.version exists in the standard library.  We use the
        # importlib-metadata backport for earlier versions of Python, but for some reason @patch doesn't
        # work when using the backport package.
        version.return_value = "1234"
        result = invoke(["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("hcoop-meetbot, version 1234")

    def test_no_args(self):
        result = invoke([])
        assert result.exit_code == 0


class TestRegenerate:
    def test_h(self):
        result = invoke(["regenerate", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["regenerate", "--help"])
        assert result.exit_code == 0

    def test_bad_config_path(self):
        with TemporaryDirectory() as temp:
            result = invoke(["regenerate", "-c", "bogus", "-r", RAW_LOG, "-d", temp])
            assert result.exit_code == 2

    def test_bad_raw_log(self):
        with TemporaryDirectory() as temp:
            result = invoke(["regenerate", "-c", CONFIG_PATH, "-r", "bogus", "-d", temp])
            assert result.exit_code == 2

    def test_bad_output_dir(self):
        result = invoke(["regenerate", "-c", CONFIG_PATH, "-r", RAW_LOG, "-d", "bogus"])
        assert result.exit_code == 2

    @patch("hcoopmeetbotlogic.writer.DATE", "2001-02-03")
    @patch("hcoopmeetbotlogic.writer.VERSION", "1.2.3")
    @patch("hcoopmeetbotlogic.cli.derive_locations")
    @patch("hcoopmeetbotlogic.cli.load_config")
    def test_regenerate(self, load_config, derive_locations):
        # The setup here (config, etc.) matches TestRendering in the writer tests.
        # That way, we can use the expected results from there to prove that the
        # regeneration works as expected, without a lot of fussy stubbing and mocking.
        # Note that CONFIG_PATH not really read due to mocking, but needs to exist on disk.
        with TemporaryDirectory() as temp:
            config = MagicMock(timezone="America/Chicago", output_format=OutputFormat.HTML)
            load_config.return_value = config
            formatted_log = Location(path=os.path.join(temp, "log.html"), url="http://log")
            formatted_minutes = Location(path=os.path.join(temp, "minutes.html"), url="http://minutes")
            locations = Locations(raw_log=RAW_LOG, formatted_log=formatted_log, formatted_minutes=formatted_minutes)
            derive_locations.return_value = locations
            result = invoke(["regenerate", "-c", CONFIG_PATH, "-r", RAW_LOG, "-d", temp])
            assert result.exit_code == 0
            load_config.assert_called_once_with(None, CONFIG_PATH)
            derive_locations.assert_called_once_with(config, ANY, RAW_LOG_PREFIX, temp)
            assert contents(formatted_log.path) == contents(EXPECTED_LOG)
            assert contents(formatted_minutes.path) == contents(EXPECTED_MINUTES)
