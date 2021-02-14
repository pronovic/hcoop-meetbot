# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

# Note: this is boilerplate code generated by supybot-plugin-create

"""
Meetbot: Plugin for Limnoria to help run IRC meetings
"""

from importlib import reload

from supybot import world
from typing import Dict

from . import config, plugin

__version__ = "0.1.0"
__author__ = "Kenneth J. Pronovici <pronovic@ieee.org>"
__contributors__ = {}  # type: Dict[str, str]
__url__ = "https://pypi.org/project/limnoria-meetbot/"

# In case we're being reloaded.
for module in [config, plugin]:
    # noinspection PyTypeChecker
    reload(module)

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure
