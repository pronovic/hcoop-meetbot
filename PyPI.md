# HCOOP Meetbot Plugin

[![pypi](https://img.shields.io/pypi/v/hcoop-meetbot.svg)](https://pypi.org/project/hcoop-meetbot/)
[![license](https://img.shields.io/pypi/l/hcoop-meetbot.svg)](https://github.com/pronovic/hcoop-meetbot/blob/master/LICENSE)
[![wheel](https://img.shields.io/pypi/wheel/hcoop-meetbot.svg)](https://pypi.org/project/hcoop-meetbot/)
[![python](https://img.shields.io/pypi/pyversions/hcoop-meetbot.svg)](https://pypi.org/project/hcoop-meetbot/)
[![Test Suite](https://github.com/pronovic/hcoop-meetbot/workflows/Test%20Suite/badge.svg)](https://github.com/pronovic/hcoop-meetbot/actions?query=workflow%3A%22Test+Suite%22)
[![docs](https://readthedocs.org/projects/hcoop-meetbot/badge/?version=stable&style=flat)](https://hcoop-meetbot.readthedocs.io/en/stable/)
[![coverage](https://coveralls.io/repos/github/pronovic/hcoop-meetbot/badge.svg?branch=master)](https://coveralls.io/github/pronovic/hcoop-meetbot?branch=master)

This is a plugin for [Limnoria](https://github.com/ProgVal/Limnoria), a bot framework for IRC.  It is designed to help run meetings on IRC.  At [HCOOP](https://hcoop.net), we use it to run our quarterly board meetings.

The code is based in part on the [MeetBot](https://github.com/rkdarst/MeetBot/) plugin for Supybot written by Richard Darst. Supybot
 is the predecessor to Limnoria.  Richard's MeetBot was "inspired by the original MeetBot, by Holger Levsen, which was itself a deri
vative of Mootbot by the Ubuntu Scribes team".  So, this code has a relatively long history.  For this version, much of the plugin w
as rewritten using Python 3, but it generally follows the pattern set by Richard's original code.  

## Using the Plugin

This plugin is distributed as a PyPI package. 

First, install Limnoria following the [instructions](https://limnoria-doc.readthedocs.io/en/latest/use/install.html).  There are also more details under [getting started](https://docs.limnoria.net/use/getting_started.html).

Choose a directory and run `supybot-wizard` to initialize a bot called `meetbot`.  Make sure to select `y` for the the question **Would you like to add an owner user for your bot?**.  You will need to identify yourself to the bot to install the plugin.  

Next, install the package from PyPI:

```
$ pip install hcoop-meetbot
```

Make sure to use `pip` (or `pip3`) for the same Python 3 installation that runs Limnoria, otherwise Limnoria won't be able to find the package.

Start Limnoria (probably with `supybot ./meetbot.conf`) and ensure that it connects to your IRC server.

Open a query to talk privately with the bot, using `/q meetbot`.  Identify yourself to the bot with `identify <user> <password>`, using the username and password you configured above via `supybot-wizard` &mdash; or use some other mechanism to identify yourself.  At this point, you have the rights to make adminstrative changes in the bot.

Install the plugin using `load HcoopMeetbot`.  You should see a response `The operation succeeded.`  At this point, you can use the `meetversion` command to confirm which version of the plugin you are using and `list HcoopMeetbot` to see information about available commands.

