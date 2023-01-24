import logging
import os.path

import click

from spaemis.commands.base import cli
from spaemis.config import load_config
from spaemis.inventory import load_inventory

logger = logging.getLogger(__name__)


@cli.command(name="project")
@click.option(
    "--config",
    help="Path to a configuration file for the scenario of interest",
    required=True,
)
@click.option("-o", "--out_dir", help="Directory to write the updated inventory")
def project_command(config, out_dir):
    """
    Generate a set of emissions projection using an emissions inventory as a base
    """

    config = load_config(config)

    inventory = load_inventory(config.inventory_name, year=config.inventory_year)

    if not os.path.exists(out_dir):
        logger.info(f"Creating output directory: {out_dir}")
        os.makedirs(out_dir, exist_ok=True)

    for slice_year in config.timeslices:
        logger.info(f"Processing year={slice_year}")
        for variable in config.variables:
            pass
