import logging
import os.path

import click

from spaemis.commands.base import cli
from spaemis.config import VariableConfig, load_config
from spaemis.inventory import EmissionsInventory, load_inventory
from spaemis.scaling import get_scaler_by_config

logger = logging.getLogger(__name__)


def scale_inventory(cfg: VariableConfig, inventory: EmissionsInventory):
    if cfg.variable not in inventory.data.variables:
        raise ValueError(f"Variable {cfg.variable} not available in inventory")

    field = inventory.data[cfg.variable].sel(sector=cfg.sector)

    scaled_field = get_scaler_by_config(cfg)(field)

    return scaled_field


@cli.command(name="project")
@click.option(
    "--config",
    help="Path to a configuration file for the scenario of interest",
    required=True,
)
@click.option("-o", "--out_dir", help="Directory to write the updated inventory")
def run_project_command(config, out_dir):
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
        for projection_config in config.variables:

            scaled_da = scale_inventory(projection_config, inventory)
