# vim: set ft=python ts=4 sw=4 expandtab:
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, MagicMock, patch

from click.testing import CliRunner, Result

from hcoopmeetbotlogic.cli import meetbot as command
from hcoopmeetbotlogic.config import OutputFormat
from hcoopmeetbotlogic.location import Location, Locations
from tests.hcoopmeetbotlogic.testdata import contents

CONFIG_PATH = str(Path(__file__).parent / "fixtures/test_config/valid/HcoopMeetbot.conf")
RAW_LOG_PREFIX = "2022-06-04"
RAW_LOG = str(Path(__file__).parent / f"fixtures/test_cli/{RAW_LOG_PREFIX}.log.json")
EXPECTED_LOG = str(Path(__file__).parent / "fixtures/test_writer/log.html")
EXPECTED_MINUTES = str(Path(__file__).parent / "fixtures/test_writer/minutes.html")


# noinspection PyTypeChecker
def invoke(args: list[str]) -> Result:
    return CliRunner().invoke(command, args)


class TestCommon:
    def test_h(self):
        result = invoke(["-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: meetbot [OPTIONS]")

    def test_help(self):
        result = invoke(["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: meetbot [OPTIONS]")

    @patch("importlib.metadata.version")  # this is used underneath by @click.version_option()
    def test_version_output(self, version):
        # This tests the --version switch, and fully verifies its output.  It will only succeed on
        # Python >= 3.9, where importlib.metadata.version exists in the standard library.  We previously
        # used the importlib-metadata backport for earlier versions of Python, but that's no longer
        # necessary.
        version.return_value = "1234"
        result = invoke(["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("hcoop-meetbot, version 1234")

    def test_no_args(self):
        result = invoke([])
        assert result.exit_code == 2
        assert result.output.startswith("Usage: meetbot [OPTIONS]")


class TestRegenerate:
    def test_h(self):
        result = invoke(["regenerate", "-h"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: meetbot regenerate [OPTIONS]")

    def test_help(self):
        result = invoke(["regenerate", "--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: meetbot regenerate [OPTIONS]")

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
            formatted_log = Location(path=str(Path(temp) / "log.html"), url="http://log")
            formatted_minutes = Location(path=str(Path(temp) / "minutes.html"), url="http://minutes")
            locations = Locations(raw_log=RAW_LOG, formatted_log=formatted_log, formatted_minutes=formatted_minutes)
            derive_locations.return_value = locations
            result = invoke(["regenerate", "-c", CONFIG_PATH, "-r", RAW_LOG, "-d", temp])
            assert result.exit_code == 0
            load_config.assert_called_once_with(None, CONFIG_PATH)
            derive_locations.assert_called_once_with(config, ANY, RAW_LOG_PREFIX, temp)
            assert contents(formatted_log.path) == contents(EXPECTED_LOG)
            assert contents(formatted_minutes.path) == contents(EXPECTED_MINUTES)
