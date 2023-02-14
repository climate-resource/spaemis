"""
Project CLI command
"""

import logging
import os.path

import click

from spaemis.commands.base import cli
from spaemis.config import DownscalingScenarioConfig, converter, load_config
from spaemis.inventory import load_inventory, write_inventory_csvs
from spaemis.project import calculate_projections

logger = logging.getLogger(__name__)


@cli.command(name="project")
@click.option(
    "--config",
    help="Path to a configuration file for the scenario of interest",
    required=True,
)
@click.option("-o", "--out-dir", help="Directory to write the updated inventory")
def run_project_command(config, out_dir):
    """
    Generate a set of emissions projection using an emissions inventory as a base
    """
    config = load_config(config)

    inventory = load_inventory(config.inventory_name, year=config.inventory_year)

    if not os.path.exists(out_dir):
        logger.info(f"Creating output directory: {out_dir}")
        os.makedirs(out_dir, exist_ok=True)

    logger.info("Saving loaded configuration to output directory")
    with open(os.path.join(out_dir, "config.yaml"), "w") as handle:
        handle.write(converter.dumps(config, DownscalingScenarioConfig))

    dataset = calculate_projections(config, inventory)

    logger.info("Writing output dataset as netcdf")
    logger.warning(dataset["CO"].sum())
    dataset.to_netcdf(os.path.join(out_dir, "projections.nc"))

    logger.info("Writing CSV files")
    for year in config.timeslices:
        target_dir = os.path.join(out_dir, str(year))
        data_to_write = dataset.sel(year=year)

        os.makedirs(target_dir, exist_ok=True)

        write_inventory_csvs(data_to_write, target_dir)
