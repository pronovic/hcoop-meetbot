# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

# Note: this must be executed by supybot-test.  Use 'run test' from the command line.
#
# Unfortunately, tests must live alongside the source code for supybot-test to execute them.
# So, this lives here rather than in the tests modules with all of the other unit tests.
# This is one of the reasons why the implementation of the actual plugin is so thin.

from unittest.mock import patch
from supybot.test import PluginTestCase
from unittest.mock import ANY
import supybot.conf as conf

def stub(context) -> None:
    context.send_reply("reply")

class HcoopMeetbotTestCase(PluginTestCase):  # type: ignore
    plugins = ("HcoopMeetbot",)

    @patch("hcoopmeetbotlogic.handler.listmeetings")
    def test_listmeetings(self, listmeetings) -> None:
        listmeetings.side_effect = stub
        self.assertNotError("listmeetings")
        listmeetings.assert_called_once() # we know it got context or stub wouldn't work

    @patch("hcoopmeetbotlogic.handler.savemeetings")
    def test_savemeetings(self, savemeetings) -> None:
        savemeetings.side_effect = stub
        self.assertNotError("savemeetings")
        savemeetings.assert_called_once() # we know it got context or stub wouldn't work

    # @patch("hcoopmeetbotlogic.handler.addchair")
    # @patch("supybot.commands.admin")
    # def test_addchair(self, admin, addchair) -> None:
    #     addchair.side_effect = stub
    #     with conf.supybot.capabilities.setValue("admin"):
    #         self.assertNotError("addchair channel nick")
    #     addchair.assert_called_once_with(ANY, "channel", ANY, "nick")
    #
    # @patch("hcoopmeetbotlogic.handler.deletemeeting")
    # def test_deletemeeting_save(self, deletemeeting) -> None:
    #     deletemeeting.side_effect = stub
    #     self.assertNotError("deletemeeting channel true")
    #     deletemeeting.assert_called_once_with(ANY, "channel", ANY, True)
    #
    # @patch("hcoopmeetbotlogic.handler.deletemeeting")
    # def test_deletemeeting_nosave(self, deletemeeting) -> None:
    #     deletemeeting.side_effect = stub
    #     self.assertNotError("deletemeeting channel false")
    #     deletemeeting.assert_called_once_with(ANY, "channel", ANY, True)
    #
    # @patch("hcoopmeetbotlogic.handler.recent")
    # def test_recent(self, recent) -> None:
    #     recent.side_effect = stub
    #     self.assertNotError("recent")
    #     recent.assert_called_once()  # we know it got context or stub wouldn't work