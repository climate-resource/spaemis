"""
generate CLI command
"""
import io
import logging
from typing import Any

import click
import pandas as pd
from yaml import safe_load

from spaemis.commands.base import cli

logger = logging.getLogger(__name__)


@cli.command(name="generate")
@click.option("--scaler", default="relative_change", help="Name of the scaler to use")
@click.option("--scaler-source", help="Source scenario for the scaler")
@click.option(
    "--mappings",
    help="YAML file containing the sector and variable mappings",
    type=click.File(),
    required=True,
)
def run_generate_command(scaler: str, scaler_source: str, mappings: Any) -> None:
    """
    Generate a scenario configuration file from a set of defaults

    This is helpful for setting up a CSV of scaling options for later tweaking
    """
    mappings = safe_load(mappings)

    sector_mapping: dict[str, str] = mappings["sectors"]
    variable_mapping: dict[str, str] = mappings["variables"]

    scaler_information = []
    for source_variable, target_variable in variable_mapping.items():
        for source_sector, target_sector in sector_mapping.items():
            scaler_information.append(
                {
                    "variable": source_variable,
                    "sector": source_sector,
                    "scaler_name": scaler,
                    "scaler_variable_id": target_variable,
                    "scaler_source_id": scaler_source,
                    "scaler_sector": target_sector,
                }
            )

    if not scaler_information:
        raise click.ClickException("No scaler information generated")
    scaler_df = pd.DataFrame(scaler_information)

    buff = io.StringIO()
    scaler_df.to_csv(buff, index=False)

    click.echo(buff.getvalue())
