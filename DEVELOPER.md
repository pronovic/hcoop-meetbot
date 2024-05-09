# Developer Notes

## Supported Platforms

This plugin was written and tested on Debian GNU/Linux, but should also work on
MacOS.  The code itself is portable, but Limnoria (Supybot) doesn't always work
as expected on Windows, so I've decided not to try.

## Architecture and Test Design

Limnoria (Supybot) plugins are quite specialized, with a standard code
structure and a dedicated test framework.  For this implementation, I have
chosen to make the Limnoria plugin in [`HcoopMeetbot`](src/HcoopMeetbot) as a
very thin wrapper over functionality implemented in the companion [`hcoopmeetbotlogic`](src/hcoopmeetbotlogic) package.  The 
interface has been abstracted, and the backend logic is not even aware of
Limnoria.  By using this design, we can minimize the testing needed to prove
that the plugin is wired up properly.  It's also easier to unit test the
business logic, and easier to apply code checks like MyPy.

There are two different test suites.  The first, in [`src/HcoopMeetbot/test.py`](src/HcoopMeetbot/test.py), is 
the Limnoria test suite.  This must be executed via `supybot-test` &mdash; you
can't run it any other way.  The second, in the [`tests`](tests) package, is a
standard Pytest suite.  The `run test` task (discussed below) executes both
suites and combines the coverage results together into a single report.

## Packaging and Dependencies

This project uses [Poetry](https://python-poetry.org/) to manage Python packaging and dependencies.  Most day-to-day tasks (such as running unit tests from the command line) are orchestrated through Poetry.

A coding standard is enforced using [Black](https://pypi.org/project/black/), [isort](https://pypi.org/project/isort/) and [Pylint](https://pypi.org/project/pylint/).  Python 3 type hinting is validated using [MyPy](https://pypi.org/project/mypy/).  To reduce boilerplate, classes are defined using [Attrs](https://www.attrs.org/) (see this [rationale](https://glyph.twistedmatrix.com/2016/08/attrs.html)).

## Pre-Commit Hooks

We rely on pre-commit hooks to ensure that the code is properly-formatted,
clean, and type-safe when it's checked in.  The `run install` step described
below installs the project pre-commit hooks into your repository.  These hooks
are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

If necessary, you can temporarily disable a hook using Git's `--no-verify`
switch.  However, keep in mind that the CI build on GitHub enforces these
checks, so the build will fail.

## Line Endings

The [`.gitattributes`](.gitattributes) file controls line endings for the files
in this repository.  Instead of relying on automatic behavior, the
`.gitattributes` file forces most files to have UNIX line endings.

## Prerequisites

Nearly all prerequisites are managed by Poetry.  All you need to do is make
sure that you have a working Python 3 enviroment and install Poetry itself.

### Poetry Version

The project is designed to work with Poetry >= 1.8.0.  If you already have an older
version of Poetry installed on your system, upgrade it first.

### MacOS

On MacOS, it's easiest to use [Homebrew](https://brew.sh/) to install Python and pipx:

```
brew install python3 pipx
```

Once that's done, make sure the `python` on your `$PATH` is Python 3 from
Homebrew (in `/usr/local`), rather than the standard Python 2 that comes with
older versions of MacOS.

Finally, install Poetry itself and then verify your installation:

```
pipx install poetry
pipx inject poetry poetry-dynamic-versioning
pipx list --include-injected
```

To upgrade this installation later, use:

```
pipx upgrade --include-injected poetry
```

### Debian

First, install Python 3 and related tools:

```
sudo apt-get install python3 python-is-python3 pipx
```

Once that's done, make sure that the `python` interpreter on your `$PATH` is
Python 3.

Finally, install Poetry itself and then verify your installation:

```
pipx install poetry
pipx inject poetry poetry-dynamic-versioning
pipx list --include-injected
```

To upgrade this installation later, use:

```
pipx upgrade --include-injected poetry
```

## Developer Tasks

The [`run`](run) script provides shortcuts for common developer tasks:

```
$ ./run --help

------------------------------------
Shortcuts for common developer tasks
------------------------------------

Basic tasks:

- run install: Setup the virtualenv via Poetry and install pre-commit hooks
- run format: Run the code formatters
- run checks: Run the code checkers
- run build: Build artifacts in the dist/ directory
- run test: Run the unit tests
- run test -c: Run the unit tests with coverage
- run test -ch: Run the unit tests with coverage and open the HTML report
- run suite: Run the complete test suite, as for the GitHub Actions CI build

Additional tasks:

- run bot: Run a bot connected to an IRC server on localhost
- run docs: Build the Sphinx documentation for readthedocs.io
- run docs -o: Build the Sphinx documentation and open in a browser
- run release: Tag and release the code, triggering GHA to publish artifacts
```

## Local Testing

Local testing is straightforward.  Instructions below are for Debian, but setup
should be similar on other platforms.

First, install an IRC server.  The [InspIRCd](https://www.inspircd.org/) server
works well and there are are Debian-specific install [instructions](https://wiki.debian.org/InspIRCd) if 
you need more help:

```
sudo apt-get install inspircd
```

Next, install an IRC client.  Any client is ok, but [Irssi](https://irssi.org/) works well:

```
sudo apt-get install irssi
```

Once the IRC server is up, make sure you can connect with the client:

```
irssi --nick=ken --connect=localhost
```

Once you are connected, join the testing channel with `/join #localtest`.

Finally, open another terminal window and run the bot:

```
$ ./run bot
Running the local bot...
INFO 2021-02-14T17:06:34 Connecting to localhost:6667.
WARNING 2021-02-14T17:06:34 Error connecting to localhost:6667: ConnectionRefusedError: [Errno 111] Connection refused
INFO 2021-02-14T17:06:34 Reconnecting to LocalNet at 2021-02-14T17:06:44.
INFO 2021-02-14T17:06:44 Connecting to localhost:6667.
INFO 2021-02-14T17:06:50 Server irc.local has version InspIRCd-2.0
INFO 2021-02-14T17:06:50 Got start of MOTD from irc.local
INFO 2021-02-14T17:06:50 Got end of MOTD from irc.local
INFO 2021-02-14T17:06:54 Join to #localtest on LocalNet synced in 4.01 seconds.
```

Notice that this takes a few seconds to complete, and there's always an initial
`ConnectionRefusedError`.  Once it's done, if you look over in your IRC window,
you should see a notification that the local bot has joined the `#localtest`
channel:

```
17:06 -!- localbot [limnoria@127.0.0.1] has joined #localtest
```

You can now interact with the local bot using `localbot: <command>`, or using
`@<command>` as a shortcut.  When you are done, use `/exit` to exit the IRC
client.

The `HcoopMeetbot` plugin is automatically available in the bot, running out of
the source tree.  If you make changes to the code, you can either reload using
`@reload HcoopMeetbot` or just CTRL-C the bot and restart it.  If reload
doesn't seem to work as expected, just use CTRL-C.

> `Note:` The first time you use `run bot`, a `localbot` directory is created
> with a `localbot.conf` file based on the original template in
> `util/localbot.conf.template`.  If something gets screwed up and you want to
> start over, just blow away the `localbot` directory and it will be recreated
> by `run bot`.

## Integration with PyCharm

Currently, I use [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download) as
my day-to-day IDE.  By integrating Black and Pylint, most everything important
that can be done from a shell environment can also be done right in PyCharm.

PyCharm offers a good developer experience.  However, the underlying configuration
on disk mixes together project policy (i.e. preferences about which test runner to
use) with system-specific settings (such as the name and version of the active Python
interpreter). This makes it impossible to commit complete PyCharm configuration
to the Git repository.  Instead, the repository contains partial configuration, and
there are instructions below about how to manually configure the remaining items.

### Prerequisites

Before going any further, make sure sure that you have installed all of the system
prerequisites discussed above.  Then, make sure your environment is in working
order.  In particular, if you do not run the install step, there will be no
virtualenv for PyCharm to use:

```
./run install && ./run suite
```

### Open the Project

Once you have a working shell development environment, **Open** (do not
**Import**) the `hcoop-meetbot` directory in PyCharm, then follow the remaining
instructions below.  By using **Open**, the existing `.idea` directory will be
retained and all of the existing settings will be used.

### Interpreter

As a security precaution, PyCharm does not trust any virtual environment
installed within the repository, such as the Poetry `.venv` directory. In the
status bar on the bottom right, PyCharm will report _No interpreter_.  Click
on this error and select **Add Interpreter**.  In the resulting dialog, click
**Ok** to accept the selected environment, which should be the Poetry virtual
environment.

### Project Structure

Go to the PyCharm settings and find the `hcoop-meetbot` project.  Under 
**Project Structure**, mark both `src` and `tests` as source folders.  In 
the **Exclude Files** box, enter the following: 

```
LICENSE;NOTICE;PyPI.md;.coverage;.coveragerc;.github;.gitignore;.gitattributes;.htmlcov;.idea;.isort.cfg;.mypy.ini;.mypy_cache;.pre-commit-config.yaml;.pylintrc;.pytest_cache;.readthedocs.yml;.tabignore;build;dist;docs/_build;out;poetry.lock;poetry.toml;run;.run;.venv;localbot;test-conf;test-data;tmp;web;backup
```

When you're done, click **Ok**.  Then, go to the gear icon in the project panel
and uncheck **Show Excluded Files**.  This will hide the files and directories
in the list above.

### Tool Preferences

In the PyCharm settings, go to **Editor > Inspections** and be sure that the
**Project Default** profile is selected.

Unit tests are written using [Pytest](https://docs.pytest.org/en/latest/),
and API documentation is written
using [Google Style Python Docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).  However,
neither of these is the default in PyCharm.  In the PyCharm settings, go to
**Tools > Python Integrated Tools**.  Under **Testing > Default test runner**,
select _pytest_.  Under **Docstrings > Docstring format**, select _Google_.

### Running Unit Tests

Right click on the `tests` folder in the project explorer and choose **Run
'pytest in tests'**.  Make sure that all of the tests pass.  If you see a slightly
different option (i.e. for "Unittest" instead of "pytest") then you probably
skipped the preferences setup discussed above.  You may need to remove the
run configuration before PyCharm will find the right test suite.

> _Note:_ Keep in mind that the specialized Limnoria test suite can only be run
> from the command line, not from within PyCharm. 

### External Tools

Optionally, you might want to set up external tools for some of common
developer tasks: code reformatting and the PyLint and MyPy checks.  One nice
advantage of doing this is that you can configure an output filter, which makes
the Pylint and MyPy errors clickable.  To set up external tools, go to PyCharm
settings and find **Tools > External Tools**.  Add the tools as described
below.

#### Shell Environment

For this to work, it's important that tools like `poetry` are on the system
path used by PyCharm.  On Linux, depending on how you start PyCharm, your
normal shell environment may or may not be inherited.  For instance, I had to
adjust the target of my LXDE desktop shortcut to be the script below, which
sources my profile before running the `pycharm.sh` shell script:

```sh
#!/bin/bash
source ~/.bash_profile
/opt/local/lib/pycharm/pycharm-community-2020.3.2/bin/pycharm.sh
```

#### Format Code

|Field|Value|
|-----|-----|
|Name|`Format Code`|
|Description|`Run the Black and isort code formatters`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`format`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Checked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Unchecked_|
|Make console active on message in stderr|_Unchecked_|
|Output filters|_Empty_|

#### Run MyPy Checks

|Field|Value|
|-----|-----|
|Name|`Run MyPy Checks`|
|Description|`Run the MyPy code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`mypy`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN$:.*`|

#### Run Pylint Checks

|Field|Value|
|-----|-----|
|Name|`Run Pylint Checks`|
|Description|`Run the Pylint code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`pylint`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN.*`|

## Release Process

### Documentation

Documentation at [Read the Docs](https://hcoop-meetbot.readthedocs.io/en/stable/)
is generated via a GitHub hook.  So, there is no formal release process for the
documentation.

### Code

Code is released to [PyPI](https://pypi.org/project/hcoop-meetbot/).  There is a
partially-automated process to publish a new release.

> _Note:_ In order to publish code, you must must have push permissions to the
> GitHub repo.

Ensure that you are on the `master` branch.  Releases must always be done from
`master`.

Ensure that the `Changelog` is up-to-date and reflects all of the changes that
will be published.  The top line must show your version as unreleased:

```
Version 0.1.29     unreleased
```

Run the release command:

```
./run release 0.1.29
```

This command updates `NOTICE` and `Changelog` to reflect the release version
and release date, commits those changes, tags the code, and pushes to GitHub.
The new tag triggers a GitHub Actions build that runs the test suite, generates
the artifacts, publishes to PyPI, and finally creates a release from the tag.

> _Note:_ This process relies on a PyPI API token with upload permissions for
> the project.  This token is stored in a GitHub Actions secret called
> `PYPI_TOKEN`.

