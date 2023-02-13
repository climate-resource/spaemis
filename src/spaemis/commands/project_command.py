"""
Project CLI command
"""

import logging
import os.path
from itertools import product
from typing import Dict, Tuple

import click
import xarray as xr

from spaemis.commands.base import cli
from spaemis.config import DownscalingScenarioConfig, VariableScalerConfig, load_config
from spaemis.inventory import EmissionsInventory, load_inventory, write_inventory_csvs
from spaemis.scaling import get_scaler_by_config

logger = logging.getLogger(__name__)


def scale_inventory(
    cfg: VariableScalerConfig, inventory: EmissionsInventory, target_year: int
) -> xr.Dataset:
    """
    Scale a given variable/sector

    Parameters
    ----------
    cfg
        Configuration used to determine how the scaling is performed
    inventory
        Emissions inventory
    target_year
        Year the data will be scaled according to

    Returns
    -------
        Dataset with a single variable with dimensions of (sector, year, lat, lon)
    """
    if cfg.variable not in inventory.data.variables:
        raise ValueError(f"Variable {cfg.variable} not available in inventory")
    if cfg.sector not in inventory.data["sector"]:
        raise ValueError(f"Sector {cfg.sector} not available in inventory")
    field = inventory.data[cfg.variable].sel(sector=cfg.sector)

    scaled_field = get_scaler_by_config(cfg.method)(
        field, inventory=inventory, target_year=target_year
    )

    scaled_field["sector"] = cfg.sector
    scaled_field["year"] = target_year

    return scaled_field.expand_dims(["sector", "year"]).to_dataset(name=cfg.variable)


def calculate_projections(
    config: DownscalingScenarioConfig, inventory: EmissionsInventory
) -> xr.Dataset:
    """
    Calculate a projected set of emissions according to some configuration

    Parameters
    ----------
    config
    inventory

    Returns
    -------
        Dataset containing the requested projections.

        The dimensionality of the output variables is (sector, year, lat, lon)
    """
    scaling_configs: Dict[Tuple[str, str], VariableScalerConfig] = {
        (cfg.variable, cfg.sector): cfg for cfg in config.scalers
    }

    if config.default_scaler:
        # Add in additional scalers for each missing variable/sector
        variables = inventory.data.data_vars.keys()
        sectors = inventory.data["sector"]

        for variable, sector in product(variables, sectors):
            scaling_configs.setdefault(
                (variable, sector),
                VariableScalerConfig(
                    variable=variable,
                    sector=sector,
                    method=config.default_scaler,
                ),
            )

    projections = []

    for variable_config in scaling_configs.values():
        for slice_year in config.timeslices:
            logger.info(
                f"Processing variable=%s sector=%s year=%i",
                variable_config.variable,
                variable_config.sector,
                slice_year,
            )
            res = scale_inventory(variable_config, inventory, slice_year)
            projections.append(res)

    # Align dims and then merge
    return xr.merge(xr.align(*projections, join="outer"))


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

    dataset = calculate_projections(config, inventory)

    for year in config.timeslices:
        target_dir = os.path.join(out_dir, str(year))
        data_to_write = dataset.sel(year=year)

        os.makedirs(target_dir, exist_ok=True)

        write_inventory_csvs(data_to_write, target_dir)
