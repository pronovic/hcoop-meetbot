# vim: set ft=python ts=4 sw=4 expandtab:
# ruff: noqa: S108

from datetime import UTC, datetime

import pytest

from hcoopmeetbotlogic.config import Config
from hcoopmeetbotlogic.location import Location, Locations, derive_locations, derive_prefix
from hcoopmeetbotlogic.meeting import Meeting


class TestLocation:
    def test_constructor(self):
        location = Location("path", "url")
        assert location.path == "path"
        assert location.url == "url"


class TestLocations:
    def test_constructor(self):
        raw_log = Location("raw-path", "raw-url")
        formatted_log = Location("log-path", "log-url")
        formatted_minutes = Location("minutes-path", "minutes-url")
        locations = Locations(raw_log, formatted_log, formatted_minutes)
        assert locations.raw_log is raw_log
        assert locations.formatted_log is formatted_log
        assert locations.formatted_minutes is formatted_minutes


class TestFunctions:
    def test_derive_prefix(self):
        path = "/path/to/whatever/something.log.json"
        assert derive_prefix(path) == "something"

    def test_derive_locations_with_constant_pattern(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="constant",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/constant.log.json"
        assert locations.raw_log.url == "https://whatever/constant.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/constant.log.html"
        assert locations.formatted_log.url == "https://whatever/constant.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/constant.html"
        assert locations.formatted_minutes.url == "https://whatever/constant.html"

    def test_derive_locations_with_prefix_override(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="constant",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting, prefix="prefix")
        assert locations.raw_log.path == "/data/meetings/hcoop/prefix.log.json"
        assert locations.raw_log.url == "https://whatever/prefix.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/prefix.log.html"
        assert locations.formatted_log.url == "https://whatever/prefix.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/prefix.html"
        assert locations.formatted_minutes.url == "https://whatever/prefix.html"

    def test_derive_locations_with_output_override(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="constant",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting, output_dir="/tmp")
        assert locations.raw_log.path == "/tmp/constant.log.json"
        assert locations.raw_log.url == "https://whatever/constant.log.json"
        assert locations.formatted_log.path == "/tmp/constant.log.html"
        assert locations.formatted_log.url == "https://whatever/constant.log.html"
        assert locations.formatted_minutes.path == "/tmp/constant.html"
        assert locations.formatted_minutes.url == "https://whatever/constant.html"

    def test_derive_locations_with_subsitution_variables(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="{id}-{name}-{founder}-{channel}-{network}",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/i-n-f-c-n.log.json"
        assert locations.raw_log.url == "https://whatever/i-n-f-c-n.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/i-n-f-c-n.log.html"
        assert locations.formatted_log.url == "https://whatever/i-n-f-c-n.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/i-n-f-c-n.html"
        assert locations.formatted_minutes.url == "https://whatever/i-n-f-c-n.html"

    def test_derive_locations_with_date_fields(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y%m%d.%H%M",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/20210307.1314.log.json"
        assert locations.raw_log.url == "https://whatever/20210307.1314.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/20210307.1314.log.html"
        assert locations.formatted_log.url == "https://whatever/20210307.1314.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/20210307.1314.html"
        assert locations.formatted_minutes.url == "https://whatever/20210307.1314.html"

    def test_derive_locations_with_normalization(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="{name}",
        )
        meeting = Meeting(
            id="i",
            name=r"!@#$%^&*()+=][}{}~`?<>,{network}\\",  # more than 1 consecutive bad char is normalized to single _
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/_network_.log.json"
        assert locations.raw_log.url == "https://whatever/_network_.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/_network_.log.html"
        assert locations.formatted_log.url == "https://whatever/_network_.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/_network_.html"
        assert locations.formatted_minutes.url == "https://whatever/_network_.html"

    def test_derive_locations_with_multiple(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y/{name}.%Y%m%d.%H%M",
        )
        meeting = Meeting(
            id="i",
            name="#n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/2021/n.20210307.1314.log.json"
        assert locations.raw_log.url == "https://whatever/2021/n.20210307.1314.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/2021/n.20210307.1314.log.html"
        assert locations.formatted_log.url == "https://whatever/2021/n.20210307.1314.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/2021/n.20210307.1314.html"
        assert locations.formatted_minutes.url == "https://whatever/2021/n.20210307.1314.html"

    def test_derive_locations_with_attempted_path_traversal_absolute(self):
        config = Config(
            conf_file=None, log_dir="/data/meetings/hcoop", url_prefix="https://whatever", timezone="UTC", pattern="/%Y%m%d.%H%M"
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        locations = derive_locations(config, meeting)
        assert locations.raw_log.path == "/data/meetings/hcoop/20210307.1314.log.json"
        assert locations.raw_log.url == "https://whatever/20210307.1314.log.json"
        assert locations.formatted_log.path == "/data/meetings/hcoop/20210307.1314.log.html"
        assert locations.formatted_log.url == "https://whatever/20210307.1314.log.html"
        assert locations.formatted_minutes.path == "/data/meetings/hcoop/20210307.1314.html"
        assert locations.formatted_minutes.url == "https://whatever/20210307.1314.html"

    def test_derive_locations_with_attempted_path_traversal_relative(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y/../../%m%d.%H%M",
        )
        meeting = Meeting(
            id="i",
            name="n",
            founder="f",
            channel="c",
            network="n",
            start_time=datetime(2021, 3, 7, 13, 14, 0, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            derive_locations(config, meeting)
