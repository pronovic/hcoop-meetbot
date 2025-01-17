# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
CLI for the meetbot tool.
"""
import os

import click

from hcoopmeetbotlogic.config import load_config
from hcoopmeetbotlogic.location import derive_locations, derive_prefix
from hcoopmeetbotlogic.meeting import Meeting
from hcoopmeetbotlogic.writer import write_formatted_log, write_formatted_minutes


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="hcoop-meetbot", prog_name="hcoop-meetbot")
def meetbot() -> None:
    """Meetbot command line utilities."""


@meetbot.command()
@click.option(
    "--config",
    "-c",
    "config_path",
    metavar="<config>",
    help="Path to config file or dir",
    required=True,
)
@click.option(
    "--raw-log",
    "-r",
    "raw_log",
    metavar="<raw-log>",
    help="Path to the raw JSON log",
    required=True,
)
@click.option(
    "--output-dir",
    "-d",
    "output_dir",
    metavar="<output-dir>",
    help="Where to write output, defaults to .",
    default=".",
)
def regenerate(config_path: str, raw_log: str, output_dir: str) -> None:
    """
    Regenerate formatted output based on a raw log file.

    This parses a raw meeting log and regenerates formatted output into
    the specified output directory.  By default, the output directory is
    the current working directory, but you can adjust that using the
    --output-dir switch.

    The formatted output will be generated based on the rules in the meetbot
    configuration file, which controls the output format, date format, time
    zone, etc.  Configuration for the file prefix is ignored and the new files
    will be generated using the exact same prefix as the raw log file itself.
    """
    if not os.path.isfile(config_path):
        raise click.UsageError("Could not find config: %s" % config_path)
    if not os.path.isfile(raw_log):
        raise click.UsageError("Could not find raw log: %s" % raw_log)
    if not os.path.isdir(output_dir):
        raise click.UsageError("Could not find output dir: %s" % output_dir)
    config = load_config(None, config_path)
    prefix = derive_prefix(raw_log)
    with open(raw_log, "r", encoding="utf-8") as fp:
        meeting = Meeting.from_json(fp.read())
    locations = derive_locations(config, meeting, prefix, output_dir)
    write_formatted_log(config, locations, meeting)
    write_formatted_minutes(config, locations, meeting)
