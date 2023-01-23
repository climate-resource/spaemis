import logging

import click

from spaemis.commands.base import cli
from spaemis.gse_emis import run_gse

logger = logging.getLogger(__name__)


@cli.command(name="gse_emis")
@click.option("--year", default=2020)
@click.option("--month", default=1)
@click.option("--day", default=1)
@click.option("-i/--in_dir", help="Directory containing a. CSV files")
@click.option("-o/--out_dir", help="Input datafiles. CSV files")
def run_gse_command(year, month, day, in_dir, out_dir):
    """
    Create a set of .run files for use by `spaemis_glo`
    """

    run_gse(year, month, day, in_dir, out_dir)
