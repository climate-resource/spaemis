import logging
from itertools import product
from typing import Dict, Tuple

import numpy as np
import scmdata
import xarray as xr

from spaemis.config import DownscalingScenarioConfig, VariableScalerConfig
from spaemis.inventory import EmissionsInventory
from spaemis.scaling import get_scaler_by_config

logger = logging.getLogger(__name__)


def scale_inventory(
    cfg: VariableScalerConfig,
    inventory: EmissionsInventory,
    target_year: int,
    timeseries: Dict[str, scmdata.ScmRun],
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
    timeseries
        Timeseries for use by proxies

    Returns
    -------
        Dataset with a single variable with dimensions of (sector, year, lat, lon)
    """
    if cfg.variable not in inventory.data.variables and not cfg.allow_missing:
        raise ValueError(f"Variable {cfg.variable} not available in inventory")
    if cfg.sector not in inventory.data["sector"] and not cfg.allow_missing:
        raise ValueError(f"Sector {cfg.sector} not available in inventory")
    try:
        field = inventory.data[cfg.variable].sel(sector=cfg.sector)
    except KeyError:
        if cfg.allow_missing:
            field = xr.DataArray(
                np.nan, coords=(inventory.data.lat, inventory.data.lon)
            )
        else:
            raise
    scaled_field = get_scaler_by_config(cfg.method)(
        data=field, inventory=inventory, target_year=target_year, timeseries=timeseries
    )

    scaled_field["sector"] = cfg.sector
    scaled_field["year"] = target_year

    return scaled_field.expand_dims(["sector", "year"]).to_dataset(name=cfg.variable)


def _create_output_data(options, config, template: xr.Dataset):
    unique_variables = sorted(set([variable for variable, _ in options]))
    unique_sectors = sorted(set([sector for _, sector in options]))
    unique_years = sorted(config.timeslices)

    coords = dict(
        sector=unique_sectors,
        year=unique_years,
        lat=template.lat,
        lon=template.lon,
    )

    return xr.Dataset(
        data_vars={
            variable: xr.DataArray(
                np.nan, coords=coords, dims=("sector", "year", "lat", "lon")
            )
            for variable in unique_variables
        },
        coords=coords,
    )


def calculate_projections(
    config: DownscalingScenarioConfig,
    inventory: EmissionsInventory,
    timeseries: Dict[str, scmdata.ScmRun],
) -> xr.Dataset:
    """
    Calculate a projected set of emissions according to some configuration

    Parameters
    ----------
    config
    inventory
    timeseries
        Optional timeseries

    Returns
    -------
        Dataset containing the requested projections.

        The dimensionality of the output variables is (sector, year, lat, lon)
    """
    scalers = config.scalers
    scaling_configs: Dict[Tuple[str, str], VariableScalerConfig] = {
        (cfg.variable, cfg.sector): cfg for cfg in scalers.get_scalers()
    }

    if scalers.default_scaler:
        # Add in additional scalers for each missing variable/sector
        variables = inventory.data.data_vars.keys()
        sectors = inventory.data["sector"].values

        for variable, sector in product(variables, sectors):
            scaling_configs.setdefault(
                (variable, sector),
                VariableScalerConfig(
                    variable=variable,
                    sector=sector,
                    method=scalers.default_scaler,
                ),
            )

    output_ds = None

    for variable_config in scaling_configs.values():
        for slice_year in config.timeslices:
            logger.info(
                "Processing variable=%s sector=%s year=%i",
                variable_config.variable,
                variable_config.sector,
                slice_year,
            )

            res = scale_inventory(variable_config, inventory, slice_year, timeseries)

            if output_ds is None:
                output_ds = _create_output_data(scaling_configs.keys(), config, res)

            output_ds[variable_config.variable].loc[
                dict(sector=variable_config.sector, year=slice_year)
            ] = (
                res[variable_config.variable]
                .sel(sector=variable_config.sector, year=slice_year)
                .values
            )

            logger.info(
                f"Sum: {output_ds[variable_config.variable].sel(sector=variable_config.sector, year=slice_year).sum().values}"
            )

    return output_ds
