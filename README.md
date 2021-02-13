# Limnoria Meetbot Plugin

[![pypi](https://img.shields.io/pypi/v/limnoria-meetbot.svg)](https://pypi.org/project/limnoria-meetbot/)
[![license](https://img.shields.io/pypi/l/limnoria-meetbot.svg)](https://github.com/pronovic/limnoria-meetbot/blob/master/LICENSE)
[![wheel](https://img.shields.io/pypi/wheel/limnoria-meetbot.svg)](https://pypi.org/project/limnoria-meetbot/)
[![python](https://img.shields.io/pypi/pyversions/limnoria-meetbot.svg)](https://pypi.org/project/limnoria-meetbot/)
[![Test Suite](https://github.com/pronovic/limnoria-meetbot/workflows/Test%20Suite/badge.svg)](https://github.com/pronovic/limnoria-meetbot/actions?query=workflow%3A%22Test+Suite%22)
[![docs](https://readthedocs.org/projects/limnoria-meetbot/badge/?version=stable&style=flat)](https://limnoria-meetbot.readthedocs.io/en/stable/)
[![coverage](https://coveralls.io/repos/github/pronovic/limnoria-meetbot/badge.svg?branch=master)](https://coveralls.io/github/pronovic/limnoria-meetbot?branch=master)

This is a plugin for [Limnoria](https://github.com/ProgVal/Limnoria), a bot framework for IRC.  It is designed to help run meetings on IRC.  At [HCoop - the Internet Hosting Cooperative](https://hcoop.net), we use it to run our quarterly board meetings.

The code is based in large part on the [MeetBot](https://github.com/rkdarst/MeetBot/) plugin for Supybot written by Richard Darst. Supybot is the predecessor to Limnoria.  Richard's MeetBot was "inspired by the original MeetBot, by Holger Levsen, which was itself a derivative of Mootbot by the Ubuntu Scribes team".  So, this code has a relatively long history.  For this version, the code was converted to modern Limnoria packaging standards, updated to support Python 3, and enhanced in other ways.  See [CREDITS](CREDITS) for Richard's original license.

Developer documentation is found in [DEVELOPER.md](DEVELOPER.md).  See that file for notes about how the code is structured, how to set up a development environment, etc.

To use the plugin, first make sure that your Limnoria installation is working properly, following the [instructions](https://docs.limnoria.net/index.html).  Next, install the plugin via pip (`pip3 install limnoria-meetbot`).  Finally, load the plugin into your Limnoria installation using `load @Meetbot`.  Refer to the [documentation](https://limnoria-meetbot.readthedocs.io/en/stable/) for more information about how to use the plugin.

