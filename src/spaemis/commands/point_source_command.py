"""
point-sources CLI command
"""
import logging

import click
import pandas as pd

from spaemis.commands.base import cli
from spaemis.config import PointSource, converter

logger = logging.getLogger(__name__)


@cli.command(name="point-source")
@click.option("--variable", default="H2")
@click.option("--sector", default="industry")
@click.option("--quantity", default=1)
@click.option("--unit", default="kg")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
def run_point_source_command(filename, variable, sector, quantity, unit):
    """
    Generate a point source configuration file from a set of locations

    This is helpful for setting up a CSV of scaling options for later tweaking
    """

    point_sources = pd.read_csv(filename)
    if point_sources.columns.isin(["lat", "lon"]).all():
        raise click.ClickException("Input file did not contain lat/lon coordinates")

    locations = [
        (lat, lon) for lat, lon in zip(point_sources["lat"], point_sources["lon"])
    ]

    ps = PointSource(
        variable=variable,
        sector=sector,
        quantity=quantity,
        unit=unit,
        location=locations,
    )

    click.echo(converter.dumps([ps]))