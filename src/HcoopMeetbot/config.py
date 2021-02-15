# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument:

# Note: this is boilerplate code generated by supybot-plugin-create

from supybot import conf

# noinspection PyBroadException
try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("HcoopMeetbot")
except:  # pylint: disable=bare-except:
    _ = lambda x: x  # placeholder that allows to run the plugin on a bot without the il8n module


def configure(advanced):
    conf.registerPlugin("HcoopMeetbot", True)


hcoopMeetbot = conf.registerPlugin("HcoopMeetbot")
