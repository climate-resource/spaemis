"""
Project a set of emissions into the future according to a set of scaling methods
"""
import itertools
import logging
from collections.abc import Iterable
from itertools import product

import numpy as np
import scmdata
import xarray as xr

from spaemis.config import DownscalingScenarioConfig, PointSource, VariableScalerConfig
from spaemis.inventory import EmissionsInventory
from spaemis.scaling import get_scaler_by_config

logger = logging.getLogger(__name__)


def scale_inventory(
    cfg: VariableScalerConfig,
    inventory: EmissionsInventory,
    target_year: int,
    timeseries: dict[str, scmdata.ScmRun],
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


def _create_output_data(
    options: Iterable[tuple[str, str]],
    config: DownscalingScenarioConfig,
    template: xr.Dataset,
) -> xr.Dataset:
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


def _process_slice(
    output_ds: xr.Dataset,
    inventory: EmissionsInventory,
    timeseries: scmdata.ScmRun,
    variable_config: VariableScalerConfig,
    year: int,
) -> None:
    logger.info(
        "Processing variable=%s sector=%s year=%i",
        variable_config.variable,
        variable_config.sector,
        year,
    )

    res = scale_inventory(variable_config, inventory, year, timeseries)

    output_ds[variable_config.variable].loc[
        dict(sector=variable_config.sector, year=year)
    ] = (
        res[variable_config.variable]
        .sel(sector=variable_config.sector, year=year)
        .values
    )
    total_emissions = (
        output_ds[variable_config.variable]
        .sel(sector=variable_config.sector, year=year)
        .sum()
        .values
    )
    logger.info(f"Total: {total_emissions / 1000 / 1000} kt / yr")


def calculate_projections(
    config: DownscalingScenarioConfig,
    inventory: EmissionsInventory,
    timeseries: dict[str, scmdata.ScmRun],
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
    scaling_configs: dict[tuple[str, str], VariableScalerConfig] = {
        (cfg.variable, cfg.sector): cfg for cfg in scalers.scalers
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

    options = itertools.product(scaling_configs.values(), config.timeslices)
    output_ds = _create_output_data(scaling_configs.keys(), config, inventory.data)

    for opt in options:
        _process_slice(output_ds, inventory, timeseries, *opt)

    return output_ds


def _process_source(
    point_source: PointSource, lat: xr.DataArray, lon: xr.DataArray
) -> xr.Dataset:
    field = xr.DataArray(coords=(lat, lon)).fillna(0)

    if point_source.unit != "kg":
        raise NotImplementedError("Only unit of kg are supported")

    num_points = len(point_source.location)
    d_lat = lat[1] - lat[0]
    for location in point_source.location:
        try:
            # TODO: check that the correct cell is being choosen
            field_location = field.sel(
                lat=location[0],
                lon=location[1],
                method="nearest",
                tolerance=np.abs(d_lat.values),
            )

            field.loc[field_location.lat, field_location.lon] += (
                point_source.quantity / num_points
            )
        except KeyError:
            # Value not in domain
            pass

    field["sector"] = point_source.sector

    # The sum of field != the requested quantity in the case that some locations are
    # outside of domain

    return field.expand_dims(["sector"]).to_dataset(name=point_source.variable)


def calculate_point_sources(
    config: DownscalingScenarioConfig, inventory: EmissionsInventory
) -> xr.Dataset:
    """
    Generate grids for point sources

    Each point source has a total quantity. This quantity is split evenly over all
    locations of that source. Values are excluded if the location falls outside of the
    domain, but still contribute to the set of locations that the quantity is spread over.

    Parameters
    ----------
    config
        Scenario configuration
    inventory
        Loaded inventory data

        These data are used for generating the latitude and longitude coordinates of the
        output grid

    Returns
    -------
    Dataset containing a gridded representation of the point source data. This Dataset
    contains the variables and sectors covered by the point sources. The sectors
    do not necessarily need to be the inventory data.
    """
    slices = []

    if config.point_sources:
        for point_source in config.point_sources.sources:
            slices.append(
                _process_source(point_source, inventory.data.lat, inventory.data.lon)
            )

        return xr.merge(slices)

    return xr.Dataset()
