HCOOP Meetbot Plugin 
====================

Release v\ |version|

.. image:: https://img.shields.io/pypi/v/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://img.shields.io/pypi/l/hcoop-meetbot.svg
    :target: https://github.com/pronovic/hcoop-meetbot/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/wheel/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://img.shields.io/pypi/pyversions/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://github.com/pronovic/hcoop-meetbot/workflows/Test%20Suite/badge.svg
    :target: https://github.com/pronovic/hcoop-meetbot/actions?query=workflow%3A%22Test+Suite%22

.. image:: https://readthedocs.org/projects/hcoop-meetbot/badge/?version=stable&style=flat
    :target: https://hcoop-meetbot.readthedocs.io/en/stable/

.. image:: https://coveralls.io/repos/github/pronovic/hcoop-meetbot/badge.svg?branch=master
    :target: https://coveralls.io/github/pronovic/hcoop-meetbot?branch=master

This is a plugin for Limnoria_, a bot framework for IRC.  It is designed to help run meetings on IRC.  At HCOOP_, we use it to run our quarterly board meetings.

The code is based in part on the MeetBot_ plugin for Supybot written by Richard Darst. Supybot is the predecessor to Limnoria.  Richard's MeetBot was "inspired by the original MeetBot, by Holger Levsen, which was itself a derivative of Mootbot by the Ubuntu Scribes team".  So, this code has a relatively long history.  For this version, much of the plugin was rewritten using Python 3, but it generally follows the pattern set by Richard's original code.

Using the Plugin
----------------

The plugin is distributed as a PyPI package.  This mechanism makes it very easy to install the plugin, but prevents us from using the standard Limnoria configuration mechanism.  This is because the ``supybot-wizard`` command is not aware of the ``HcoopMeetbot`` plugin.  Instead, you have to create a small ``.conf`` file on disk to configure the plugin.

Install and Configure Limnoria
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install Limnoria following the instructions_.  There are also more details under getting-started_.

Choose a directory and run ``supybot-wizard`` to initialize a bot called ``meetbot``.  Make sure to select ``y`` for the the question **Would you like to add an owner user for your bot?**  You will need to identify yourself to the bot to install the plugin.  

Install and Configure HcoopMeetbot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the package from PyPI::

   $ pip install hcoop-meetbot

Make sure to use ``pip`` (or ``pip3``) for the same Python 3 installation that runs Limnoria, otherwise Limnoria won't be able to find the package.

Next, add configuration.  Create a file ``HcoopMeetbot.conf`` in the ``conf`` directory for your Limnoria bot.  Fill four values into the file::

   [HcoopMeetbot]
   logDir = /home/myuser/meetings
   urlPrefix = https://example.com/meetings
   pattern = %Y/{name}.%Y%m%d.%H%M
   timezone = UTC

If you skip this step and don't create a config file, the plugin will try to use sensible defaults as shown below.

+---------------+----------------------------------------+----------------------------------------------------------------------+
| Parameter     | Default Value                          | Description                                                          |
+===============+========================================+======================================================================+
| ``logDir``    | ``$HOME/hcoop-meetbot``                | Absolute path where meeting logs will be written on disk.            |
+---------------+----------------------------------------+----------------------------------------------------------------------+
| ``urlPrefix`` | ``/``                                  | URL prefix to place on generated links to logfiles that are reported |
|               |                                        | when the meeting ends.  This can be a simple path, but it is more    |
|               |                                        | useful if you set it to the base URL where the files will be served  |
|               |                                        | from, so participants see the entire public URL.                     |
+---------------+----------------------------------------+----------------------------------------------------------------------+
| ``pattern``   | ``%Y/{name}.%Y%m%d.%H%M``              | Pattern for files generated in ``logDir``. The following variables   |
|               |                                        | may be used to substitute in attributes of the meeting: ``{id}``     |
|               |                                        | ``{name}``, ``{channel}``, ``{network}``, and ``{founder}``.         |
|               |                                        | Additionally, you may use strftime_ codes for date fields from the   |
|               |                                        | meeting start date. *Unlike* with the original MeetBot, you do *not* |
|               |                                        | need to double the ``%`` characters.  The meeting name defaults to   |
|               |                                        | the channel.  Anywhere in the path, only ``./a-zA-Z0-9_-`` are       |
|               |                                        | allowed, and any other character will be replaced with ``_``.  You   |
|               |                                        | may imply a subdirectory by using the ``/`` character as a path      |
|               |                                        | separator, but directory traversal is not allowed, and the resulting |
|               |                                        | file must be within ``logDir``.                                      |
+---------------+----------------------------------------+----------------------------------------------------------------------+
| ``timezone``  | ``UTC``                                | The timezone to use for files names and in generated content.        |
|               |                                        | May be any standard IANA_ value, like ``UTC``, ``US/Eastern``,       |
|               |                                        | or ``America/Chicago``, etc.                                         |
+---------------+----------------------------------------+----------------------------------------------------------------------+

Run the Bot
~~~~~~~~~~~

Start Limnoria (for instance with ``supybot ./meetbot.conf``) and ensure that it connects to your IRC server.

Open a query to talk privately with the bot, using ``/q meetbot``.  Identify yourself to the bot with ``identify <user> <password>``, using the username and password you configured above via ``supybot-wizard`` - or use some other mechanism to identify yourself.  At this point, you have the rights to make adminstrative changes in the bot.

Install the plugin using ``load HcoopMeetbot``.  You should see a response ``The operation succeeded.``  At this point, you can use the ``meetversion`` command to confirm which version of the plugin you are using and ``list HcoopMeetbot`` to see information about available commands::

   (localhost)
   02:22 -!- Irssi: Starting query in localhost with meetbot
   02:22 <ken> identify ken thesecret
   02:22 -meetbot(limnoria@127.0.0.1)- The operation succeeded.
   02:22 <ken> load HcoopMeetbot
   02:22 -meetbot(limnoria@127.0.0.1)- The operation succeeded.
   02:22 <ken> meetversion
   02:22 -meetbot(limnoria@127.0.0.1)- HcoopMeetbot v0.1.0, released 16 Feb 2021
   02:22 <ken> list HcoopMeetbot
   02:22 -meetbot(limnoria@127.0.0.1)- addchair, deletemeeting, listmeetings, meetversion, recent, and savemeetings

   [02:22] [ken(+i)] [2:localhost/meetbot]
   [meetbot]

Then you can join any channel that the Limnoria bot is configured to join, and start using the plugin immediately.

Later, if you update the plugin (``pip install --upgrade``), you can either stop and start the bot process, or use ``@reload HcoopMeetbot`` from within IRC.  You may need to identify yourself to Limnoria before doing this.


Developer Documentation
-----------------------

.. toctree::
   :maxdepth: 2
   :glob:

.. _Limnoria: https://github.com/ProgVal/Limnoria
.. _HCOOP: https://hcoop.net/
.. _MeetBot: https://github.com/rkdarst/MeetBot/
.. _instructions: https://limnoria-doc.readthedocs.io/en/latest/use/install.html
.. _getting-started: https://docs.limnoria.net/use/getting_started.html
.. _strftime: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
.. _IANA: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

