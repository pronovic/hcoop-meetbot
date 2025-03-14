HCoop Meetbot Plugin 
====================

Release v\ |version|

.. image:: https://img.shields.io/pypi/v/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://img.shields.io/pypi/l/hcoop-meetbot.svg
    :target: https://github.com/pronovic/hcoop-meetbot/blob/main/LICENSE

.. image:: https://img.shields.io/pypi/wheel/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://img.shields.io/pypi/pyversions/hcoop-meetbot.svg
    :target: https://pypi.org/project/hcoop-meetbot/

.. image:: https://github.com/pronovic/hcoop-meetbot/workflows/Test%20Suite/badge.svg
    :target: https://github.com/pronovic/hcoop-meetbot/actions?query=workflow%3A%22Test+Suite%22

.. image:: https://readthedocs.org/projects/hcoop-meetbot/badge/?version=stable&style=flat
    :target: https://hcoop-meetbot.readthedocs.io/en/stable/

.. image:: https://coveralls.io/repos/github/pronovic/hcoop-meetbot/badge.svg?branch=main
    :target: https://coveralls.io/github/pronovic/hcoop-meetbot?branch=main

hcoop-meetbot_ is a plugin for Limnoria_, a bot framework for IRC.  It is designed to help run meetings on IRC.  It was originally written for quarterly board meetings at HCoop_, when Ken was on the board there.

The code is based in part on the MeetBot_ plugin for Supybot written by Richard Darst. Supybot is the predecessor to Limnoria.  Richard's MeetBot was "inspired by the original MeetBot, by Holger Levsen, which was itself a derivative of Mootbot by the Ubuntu Scribes team".  So, this code has a relatively long history.  For this version, much of the plugin was rewritten using Python 3, but it generally follows the pattern set by Richard's original code.

Developer Documentation
-----------------------

.. toctree::
   :maxdepth: 2
   :glob:

Running a Meeting
-----------------

If the plugin is already installed in your IRC channel, running a meeting is easy.  Meeting commands all start with ``#``, and
are mostly compatible with the original MeetBot.  

*Note:* Not all commands give feedback, and you won't be warned about invalid commands unless a meeting is active.

Basic Meeting
~~~~~~~~~~~~~

You can run a basic meeting with just these few commands.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#startmeeting`` | Anyone | Start a new meeting.  The user who starts the meeting becomes its chair.                           |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#endmeeting``   | Chair  | End the active meeting. Writes log and minutes to the configured log directory.                    |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#topic``        | Chair  | Set a new discussion topic like ``#topic First Topic``.  Events are grouped together under topics  |
|                   |        | in the minutes.                                                                                    |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#accepted``     | Chair  | Document an agreement in the minutes, like ``#accepted We agree to disagree``.                     |
+-------------------+--------+----------------------------------------------------------------------------------------------------+

Attendance
~~~~~~~~~~

You can optionally document attendance using these commands.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#here``         | Anyone | Document attendance and optionally associate an IRC nickname to an alias.  If IRC nick ``ken``     |
|                   |        | uses ``#here``, that nick is marked as a meeting attendee in the minutes.  If IRC nick ``ken``     |
|                   |        | includes an alias, like ``#here pronovic`` or ``#here Ken Pronovici``, then the remainder          |
|                   |        | of the line becomes an alias for ``ken`` and can be used when assigning actions. Although          |
|                   |        | aliases can contain whitespace (like ``Ken Pronovici`` as shown in the example above), it's        |
|                   |        | best to avoid this.  A camel-case identifier like ``KenPronovici`` is less ambiguous.              |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#nick``         | Chair  | Identify an IRC nickname for a user who hasn't spoken, so they can be assigned actions, like       |
|                   |        | ``#nick whoever``.                                                                                 |
+-------------------+--------+----------------------------------------------------------------------------------------------------+

*Note:* When generating the minutes, nicks and aliases are always matched
case-insensitively, as in IRC itself.


Agreement and Disagrement
~~~~~~~~~~~~~~~~~~~~~~~~~

You can document agreement and disagreement using these commands.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#accepted``     | Chair  | Document an agreement in the minutes, like ``#accepted We agree to disagree``.                     |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#failed``       | Chair  | Document disagreement in the minutes, like ``#failed Budget was not approved``.                    |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#inconclusive`` | Chair  | Document a decision that could not be made, like ``#inconclusive There was no agreement on a fix``.|
+-------------------+--------+----------------------------------------------------------------------------------------------------+

Formal Voting
~~~~~~~~~~~~~

If you are running a formal meeting, you can document a motion and take votes using these commands.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#motion``       | Chair  | Indicate that a motion has been made, like ``#motion Approve the 2021 budget``.                    |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#vote``         | Anyone | Vote in favor of or against the motion, like ``#vote +1`` or ``#vote -1``.                         |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#close``        | Chair  | Close voting on the open motion, and report voting results.                                        | 
+-------------------+--------+----------------------------------------------------------------------------------------------------+

Important Information
~~~~~~~~~~~~~~~~~~~~~

Anyone can use these commands to log important information in the minutes.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#info``         | Anyone | Log important information in the minutes, like ``#info Happy hour starts at 6pm``.                 |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#action``       | Anyone | Document an action, like ``#action ken will pick up dinner`` or ``#action ken and ed own snacks``. |
|                   |        | If you include one or more unambiguous nicks or aliases in the action text, the action will be     |
|                   |        | assigned to those user(s). See below for some caveats.                                             |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#idea``         | Anyone | Add an idea to the minutes, like ``#idea we should start using HCoop Meetbot``.                    |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#help``         | Anyone | Add a call for help into the minutes. Use this command when you need to recruit someone to do a    |
|                   |        | task. (Counter-intuitively, this does not not provide help for how to use the bot.)                |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#link``         | Anyone | Add a link to the meeting minutes.  Additionally, certain common URL patterns are auto-detected    |
|                   |        | even if you do not use ``#link``.  Use like ``#link https://whatever.com/agenda.html`` or          |
|                   |        | ``#link Agenda at https://whatever/agenda.html like usual``. The URL portion of the                |
|                   |        | message will be turned into an ``<a href>`` in the generated minutes.                              |
+-------------------+--------+----------------------------------------------------------------------------------------------------+

*Note:* When you document an action with ``#action``, the bot will try to
identify any nick or alias associated with that action, so it can be listed in
the **Action Items by Attendee** section of the minutes.  This works for any
nick or alias identified with ``#here`` or ``#nick``, but *only* if the nick or
alias can be identified *unambiguously* in the action text --- either
surrounded by whitespace or found at the very start or end of the text.  There
are also some special cases for common constructs like parenthesis and colons.
To avoid confusion, it's best to make your action text as simple and as clear
as possible. Remember that nicks and aliases are matched case-insensitively, as
in IRC itself.

Administrative Commands
~~~~~~~~~~~~~~~~~~~~~~~

A meeting chair may run a variety of administrative commands.

+-------------------+--------+----------------------------------------------------------------------------------------------------+
| Command           | Who?   | Description                                                                                        |
+===================+========+====================================================================================================+
| ``#meetingname``  | Chair  | By default, the meeting name is set to the channel name.  Use ``#meetingname`` to set an           |
|                   |        | alternate name, which will be indicated in the minutes and may be used in the generated file       |
|                   |        | names (depending on configuration).                                                                |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#chair``        | Chair  | Add an IRC nickname to the list of meeting chairs.                                                 |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#unchair``      | Chair  | Remove an IRC nickname from the list of meeting chairs.                                            |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#undo``         | Chair  | Remove the most recent event (such as ``#accepted``, ``#topic``, ``#info``, etc.) from the         |
|                   |        | minutes.  The activity will still appear in the raw log, but won't be called out in the summary.   |
+-------------------+--------+----------------------------------------------------------------------------------------------------+
| ``#save``         | Chair  | Save the meeting to disk in its current state, without calling ``#endmeeting``.  Some results      |
|                   |        | might look a little funky, like ``None`` for the meeting end date.                                 |
+-------------------+--------+----------------------------------------------------------------------------------------------------+

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

+---------------------+---------------------------+------------------------------------------------------------------------+
| Parameter           | Default Value             | Description                                                            |
+=====================+===========================+========================================================================+
| ``logDir``          | ``$HOME/hcoop-meetbot``   | Absolute path where meeting logs will be written on disk.              |
+---------------------+---------------------------+------------------------------------------------------------------------+
| ``urlPrefix``       | ``/``                     | URL prefix to place on generated links to logfiles that are reported   |
|                     |                           | when the meeting ends.  This can be a simple path, but it is more      |
|                     |                           | useful if you set it to the base URL where the files will be served    |
|                     |                           | from, so participants see the entire public URL.                       |
+---------------------+---------------------------+------------------------------------------------------------------------+
| ``pattern``         | ``%Y/{name}.%Y%m%d.%H%M`` | Pattern for files generated in ``logDir``. The following variables     |
|                     |                           | may be used to substitute in attributes of the meeting: ``{id}``       |
|                     |                           | ``{name}``, ``{channel}``, ``{network}``, and ``{founder}``.           |
|                     |                           | Additionally, you may use strftime_ codes for date fields from the     |
|                     |                           | meeting start date. *Unlike* with the original MeetBot, you do *not*   |
|                     |                           | need to double the ``%`` characters.  The meeting name defaults to     |
|                     |                           | the channel.  Anywhere in the path, only ``./a-zA-Z0-9_-`` are         |
|                     |                           | allowed, and any other character will be replaced with ``_``.  You     |
|                     |                           | may imply a subdirectory by using the ``/`` character as a path        |
|                     |                           | separator, but directory traversal is not allowed, and the resulting   |
|                     |                           | file must be within ``logDir``.                                        |
+---------------------+---------------------------+------------------------------------------------------------------------+
| ``timezone``        | ``UTC``                   | The timezone to use for files names and in generated content.          |
|                     |                           | May be any standard IANA_ value, like ``UTC``, ``US/Eastern``,         |
|                     |                           | or ``America/Chicago``, etc.                                           |
+---------------------+---------------------------+------------------------------------------------------------------------+
| ``useChannelTopic`` | ``False``                 | Whether the bot should use the channel topic. If set to ``True``,      |
|                     |                           | the bot will attempt to change the channel topic when the meeting      |
|                     |                           | starts, when it ends, and whenever the ``#topic`` command is used.     |
|                     |                           | This often fails with an error like ``You're not a channel operator``, |
|                     |                           | shown in the Limnoria logs.  However, if you know your bot does have   |
|                     |                           | permissions to set the channel topic, then can set this to ``True``    | 
|                     |                           | and the topic will be updated to reflect the state of the meeting.     |
+---------------------+---------------------------+------------------------------------------------------------------------+
| ``outputFormat``    | ``HTML``                  | The output format to use.  Optional. Currently, the only allowed value |
|                     |                           | is ``HTML``, but it's configurable to facilitate future enhancements.  |
+---------------------+---------------------------+------------------------------------------------------------------------+

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
   02:22 -meetbot(limnoria@127.0.0.1)- HcoopMeetbot v0.1.0 (17 Mar 2021)
   02:22 <ken> list HcoopMeetbot
   02:22 -meetbot(limnoria@127.0.0.1)- addchair, deletemeeting, listmeetings, meetversion, recent, and savemeetings

   [02:22] [ken(+i)] [2:localhost/meetbot]
   [meetbot]

Then you can join any channel that the Limnoria bot is configured to join, and start using the plugin immediately.

Later, if you update the plugin (``pip install --upgrade``), you can either stop and start the bot process, or use ``@reload HcoopMeetbot`` from within IRC.  You may need to identify yourself to Limnoria before doing this.

Administrator Features
----------------------

The administrator who owns the Limnoria bot has access to some additional features and can manage meetings across multiple channels.  These commands are invoked in the traditional way, either by addressing the bot by its name or using the command prefix you configured when setting up the bot (often ``@``).  These commands work in any channel the bot has joined, and do not require a meeting to be active.

+-------------------+-------------------------------------------------------------------------------------------------------------+
| Command           | Description                                                                                                 |
+===================+=============================================================================================================+
| ``commands``      | List all of the legal meeting commands (``#startmeeting``, ``#endmeeting``, etc.).                          |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``meetversion``   | Reply with the version of the bot that is running.                                                          |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``listmeetings``  | List all of the active meetings in all channels.                                                            |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``recent``        | List all of the recently-completed meetings in all channels.                                                |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``savemeetings``  | Save all currently active meetings, like a chair calling ``#save`` individually for each meeting.  All of   |
|                   | the same caveats that apply to ``#save`` also apply here.                                                   |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``addchair``      | Add an IRC nickname to the list of chairs for a meeting in a channel, like ``@addchair #channel nick``.     |
+-------------------+-------------------------------------------------------------------------------------------------------------+
| ``deletemeeting`` | Delete a meeting, moving it out of active state without actually ending it, like                            |
|                   | ``@deletemeeting #channel``.  By default, it will be saved before being deleted.  If you don't want that,   |
|                   | then use ``@deletemeeting #channel false``.                                                                 |
+-------------------+-------------------------------------------------------------------------------------------------------------+

Command Line Tool
-----------------

The Python package ships with a command line tool named ``meetbot``.  This tool
implements utilities to be used outside of IRC::

   $ meetbot --help
   Usage: meetbot [OPTIONS] COMMAND [ARGS]...

     Meetbot command line utilities.

   Options:
     --version   Show the version and exit.
     -h, --help  Show this message and exit.

   Commands:
     regenerate  Regenerate formatted output based on a raw log file.

Currently, the only utility available is ``regenerate``::

   $ meetbot regenerate --help
   Usage: meetbot regenerate [OPTIONS]

     Regenerate formatted output based on a raw log file.

     This parses a raw meeting log and regenerates formatted output into the
     specified output directory.  By default, the output directory is the current
     working directory, but you can adjust that using the --output-dir switch.

     The formatted output will be generated based on the rules in the meetbot
     configuration file, which controls the output format, date format, time
     zone, etc.  Configuration for the file prefix is ignored and the new files
     will be generated using the exact same prefix as the raw log file itself.

   Options:
     -c, --config <config>          Path to config file or dir  [required]
     -r, --raw-log <raw-log>        Path to the raw JSON log  [required]
     -d, --output-dir <output-dir>  Where to write output, defaults to .
     -h, --help                     Show this message and exit.

You can use this as an error-recovery tool (if for some reason the bot
crashes when generating formatted output) or as a way to take advantage
of new features in the bot (for instance, if output has been improved
or there is a new output format).

*Note:* This utility only works for meetings that were run using v0.6.0 or
later of the plugin, since earlier versions do not generate the raw JSON
meeting log that is used as input.  

.. _hcoop-meetbot: https://github.com/pronovic/hcoop-meetbot
.. _Limnoria: https://github.com/ProgVal/Limnoria
.. _HCoop: https://hcoop.net/
.. _MeetBot: https://github.com/rkdarst/MeetBot/
.. _instructions: https://limnoria-doc.readthedocs.io/en/latest/use/install.html
.. _getting-started: https://docs.limnoria.net/use/getting_started.html
.. _strftime: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
.. _IANA: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

