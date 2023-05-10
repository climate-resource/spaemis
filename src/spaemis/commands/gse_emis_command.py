"""
GSE emis CLI command
"""
import logging
import os

import click

from spaemis.commands.base import cli
from spaemis.gse_emis import run_gse

logger = logging.getLogger(__name__)


@cli.command(name="gse_emis")
@click.option("--year", default=2020)
@click.option("--month", default=1)
@click.option("--day", default=1)
@click.option("-i", "--in_dir", help="Directory containing a. CSV files", type=str)
@click.option("-o", "--out_dir", help="Input datafiles. CSV files", type=str)
def run_gse_command(year: int, month: int, day: int, in_dir: str, out_dir: str) -> None:
    """
    Create a set of .run files for use by `spaemis_glo`
    """
    os.makedirs(out_dir, exist_ok=True)

    run_gse(year, month, day, in_dir, out_dir)
