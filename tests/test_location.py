# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=no-self-use,protected-access
from datetime import datetime

import pytest

from hcoopmeetbotlogic.config import Config
from hcoopmeetbotlogic.location import Location, Locations, derive_locations
from hcoopmeetbotlogic.meeting import Meeting


class TestLocation:
    def test_constructor(self):
        location = Location("path", "url")
        assert location.path == "path"
        assert location.url == "url"


class TestLocations:
    def test_constructor(self):
        log = Location("log-path", "log-url")
        minutes = Location("minutes-path", "minutes-url")
        locations = Locations(log, minutes)
        assert locations.log is log
        assert locations.minutes is minutes


class TestFunctions:
    def test_derive_locations_with_constant_pattern(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="constant",
        )
        meeting = Meeting(id="i", name="n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/constant.log.html"
        assert locations.log.url == "https://whatever/constant.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/constant.html"
        assert locations.minutes.url == "https://whatever/constant.html"

    def test_derive_locations_with_subsitution_variables(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="{id}-{name}-{founder}-{channel}-{network}",
        )
        meeting = Meeting(id="i", name="n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/i-n-f-c-n.log.html"
        assert locations.log.url == "https://whatever/i-n-f-c-n.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/i-n-f-c-n.html"
        assert locations.minutes.url == "https://whatever/i-n-f-c-n.html"

    def test_derive_locations_with_date_fields(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y%m%d.%H%M",
        )
        meeting = Meeting(id="i", name="n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/20210307.1314.log.html"
        assert locations.log.url == "https://whatever/20210307.1314.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/20210307.1314.html"
        assert locations.minutes.url == "https://whatever/20210307.1314.html"

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
            start_time=datetime(2021, 3, 7, 13, 14, 0),
        )
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/_network_.log.html"
        assert locations.log.url == "https://whatever/_network_.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/_network_.html"
        assert locations.minutes.url == "https://whatever/_network_.html"

    def test_derive_locations_with_multiple(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y/{name}.%Y%m%d.%H%M",
        )
        meeting = Meeting(id="i", name="#n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/2021/n.20210307.1314.log.html"
        assert locations.log.url == "https://whatever/2021/n.20210307.1314.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/2021/n.20210307.1314.html"
        assert locations.minutes.url == "https://whatever/2021/n.20210307.1314.html"

    def test_derive_locations_with_attempted_path_traversal_absolute(self):
        config = Config(
            conf_file=None, log_dir="/data/meetings/hcoop", url_prefix="https://whatever", timezone="UTC", pattern="/%Y%m%d.%H%M"
        )
        meeting = Meeting(id="i", name="n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        locations = derive_locations(config, meeting)
        assert locations.log.path == "/data/meetings/hcoop/20210307.1314.log.html"
        assert locations.log.url == "https://whatever/20210307.1314.log.html"
        assert locations.minutes.path == "/data/meetings/hcoop/20210307.1314.html"
        assert locations.minutes.url == "https://whatever/20210307.1314.html"

    def test_derive_locations_with_attempted_path_traversal_relative(self):
        config = Config(
            conf_file=None,
            log_dir="/data/meetings/hcoop",
            url_prefix="https://whatever",
            timezone="UTC",
            pattern="%Y/../../%m%d.%H%M",
        )
        meeting = Meeting(id="i", name="n", founder="f", channel="c", network="n", start_time=datetime(2021, 3, 7, 13, 14, 0))
        with pytest.raises(ValueError):
            derive_locations(config, meeting)
