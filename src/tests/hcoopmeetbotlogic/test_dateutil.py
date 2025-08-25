# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from datetime import datetime

from hcoopmeetbotlogic.dateutil import formatdate, now


class TestDateFunctions:
    def test_now(self):
        assert now().utcoffset().total_seconds() == 0  # timestamp should be in UTC

    def test_format_date(self):
        timestamp = datetime(2021, 3, 7, 13, 14, 0)  # in UTC by default
        assert formatdate(timestamp, zone="UTC") == "2021-03-07T13:14+0000"
        assert formatdate(timestamp, zone="America/Chicago") == "2021-03-07T07:14-0600"
        assert formatdate(timestamp, zone="US/Eastern") == "2021-03-07T08:14-0500"
