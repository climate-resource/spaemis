"""
Proxy scaler

A proxy scaler uses a proxy (a 2d pattern) to disaggregate an emissions timeseries over a target area.

The proxy must cover the area of interest of the emissions timeseries
"""
import logging
import os
from typing import Any, Dict, List

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import TimeseriesMethod
from spaemis.constants import PROCESSED_DATA_DIR
from spaemis.input_data import _apply_filters
from spaemis.inventory import EmissionsInventory, load_inventory
from spaemis.unit_registry import convert_to_target_unit, unit_registry
from spaemis.utils import clip_region

from .base import BaseScaler


def get_proxy(proxy_name: str, inventory: EmissionsInventory, **kwargs) -> xr.DataArray:
    root_dir = os.path.join(PROCESSED_DATA_DIR, "proxies")

    proxy_toks = proxy_name.split("|")

    proxies = {
        "population": os.path.join(
            root_dir,
            "sedacs",
            "popdynamics-base_year-2000-rev01-byr.nc",
        ),
        "residential_density": os.path.join(
            root_dir,
            "ga",
            "NEXIS_Residential_Dwelling_Density.nc",
        ),
    }

    if proxy_toks[0] in proxies:
        return xr.load_dataset(proxies[proxy_toks[0]])[proxy_toks[0]]
    elif proxy_toks[0] == "inventory":
        sector = proxy_toks[1]
        return inventory.data["NOx"].sel(sector=sector)
    elif proxy_toks[0] == "australian_inventory":
        aus_inv = load_inventory("australia", 2016)
        sector = proxy_toks[1]
        return aus_inv.data["NOx"].sel(sector=sector)


def get_timeseries(timeseries, source, filters, target_year) -> scmdata.ScmRun:
    try:
        ts = timeseries[source]
    except KeyError as exc:
        raise ValueError(f"Source dataset is not loaded: {source}") from exc

    # This linearly interpolates the timeseries
    ts = _apply_filters(ts, filters).resample("AS")

    if len(ts) == 0:
        raise ValueError(f"No data matching {filters} was found in {source} input data")

    if len(ts) > 1:
        raise ValueError(
            f"More than one match was found for {filters} in {source} input data"
        )

    if target_year not in ts["year"].values:
        raise ValueError(f"No timeseries data for year={target_year} available")

    ts = ts.filter(year=target_year)

    if ts.shape != (1, 1):
        raise AssertionError("Something went wrong when filtering timeseries")
    return ts


def _check_unit(unit: str):
    unit = unit_registry(unit)

    msg = "Expected unit of the form [X] * [mass] / [time]"

    if (
        len(unit.dimensionality) != 3
        and unit.dimensionality["[mass]"] != 1
        and unit.dimensionality["[time]"] != -1
        and "[length]" not in unit.dimensionality
    ):
        raise ValueError(msg)


def apply_amount(amount: float, unit: str, proxy: xr.DataArray) -> xr.DataArray:
    # Verify units are [X] * [mass] / [time]
    _check_unit(unit)

    logging.debug(f"applying {amount} {unit} using a proxy")

    # Adjust to kg X/yr
    scale_factor = convert_to_target_unit(unit, target_unit="kg")
    amount = amount * scale_factor.m

    # Calculate density map
    proxy_density = proxy / proxy.sum()

    scaled = amount * proxy_density
    scaled.attrs["units"] = str(scale_factor.u) + " / cell"

    return scaled


@define
class TimeseriesScaler(BaseScaler):
    """
    Scale a spatial pattern using a timeseries
    """

    proxy: str
    proxy_region: str
    source_timeseries: str
    source_filters: List[Dict[str, Any]]

    def __call__(
        self,
        *,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        timeseries: Dict[str, scmdata.ScmRun],
        target_year: int,
        **kwargs,
    ) -> xr.DataArray:
        """
        Apply scaling

        Parameters
        ----------
        data
            Timeseries to scale
        inventory
        timeseries
            Timeseries data used by the proxy
        kwargs

        Returns
        -------

        """
        ts = get_timeseries(
            timeseries,
            self.source_timeseries,
            self.source_filters,
            target_year=target_year,
        )

        proxy_region = get_proxy(self.proxy_region, inventory=inventory)
        proxy_region_clipped = clip_region(proxy_region, inventory.border_mask)
        region_share = proxy_region_clipped.sum() / proxy_region.sum()

        proxy = clip_region(
            get_proxy(self.proxy, inventory=inventory), inventory.border_mask
        )
        proxy_interp = proxy.interp(lat=data.lat, lon=data.lon)

        unit = ts.get_unique_meta("unit", True)
        amount = ts.values.squeeze() * region_share
        return apply_amount(amount, unit, proxy_interp)

    @classmethod
    def create_from_config(cls, method: TimeseriesMethod) -> "TimeseriesScaler":
        return TimeseriesScaler(
            proxy=method.proxy,
            proxy_region=method.proxy_region or method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters=method.source_filters,
        )
