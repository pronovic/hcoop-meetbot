Limnoria Meetbot Plugin 
=======================

Release v\ |version|

.. image:: https://img.shields.io/pypi/v/limnoria-meetbot.svg
    :target: https://pypi.org/project/limnoria-meetbot/

.. image:: https://img.shields.io/pypi/l/limnoria-meetbot.svg
    :target: https://github.com/pronovic/limnoria-meetbot/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/wheel/limnoria-meetbot.svg
    :target: https://pypi.org/project/limnoria-meetbot/

.. image:: https://img.shields.io/pypi/pyversions/limnoria-meetbot.svg
    :target: https://pypi.org/project/limnoria-meetbot/

.. image:: https://github.com/pronovic/limnoria-meetbot/workflows/Test%20Suite/badge.svg
    :target: https://github.com/pronovic/limnoria-meetbot/actions?query=workflow%3A%22Test+Suite%22

.. image:: https://readthedocs.org/projects/limnoria-meetbot/badge/?version=stable&style=flat
    :target: https://limnoria-meetbot.readthedocs.io/en/stable/

.. image:: https://coveralls.io/repos/github/pronovic/limnoria-meetbot/badge.svg?branch=master
    :target: https://coveralls.io/github/pronovic/limnoria-meetbot?branch=master

This is a plugin for Limnoria_, a bot framework for IRC.  It is designed to help run meetings on IRC.  At HCoop_ - the Internet Hosting Cooperative, we use it to run our quarterly board meetings.

The code is based in large part on the MeetBot_ plugin for Supybot written by Richard Darst. Supybot is the predecessor to Limnoria.  Richard's MeetBot was "inspired by the original MeetBot, by Holger Levsen, which was itself a derivative of Mootbot by the Ubuntu Scribes team".  So, this code has a relatively long history.  For this version, the code was converted to modern Limnoria packaging standards, updated to support Python 3, and enhanced in other ways.

To use the plugin, first make sure that your Limnoria installation is working properly, following the instructions_.  Next, install the plugin via pip (``pip3 install limnoria-meetbot``).  Finally, load the plugin into your Limnoria installation using ``load @Meetbot``.  

Developer Documentation
-----------------------

.. toctree::
   :maxdepth: 2
   :glob:

.. _Limnoria: https://github.com/ProgVal/Limnoria
.. _HCoop: https://hcoop.net/
.. _MeetBot: https://github.com/rkdarst/MeetBot/
.. _instructions: https://docs.limnoria.net/index.html
.. _PyPI: https://pypi.org/project/limnoria-meetbot/#files

