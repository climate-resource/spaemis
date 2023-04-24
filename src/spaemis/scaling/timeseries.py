"""
Timeseries scaler.

A timeseries scaler uses a proxy (a 2d pattern) to disaggregate an emissions timeseries over
 a target area.

The proxy must cover the area of interest of the emissions timeseries
"""
import logging
from typing import Any

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import TimeseriesMethod
from spaemis.input_data import _apply_filters
from spaemis.inventory import EmissionsInventory
from spaemis.unit_registry import convert_to_target_unit, unit_registry
from spaemis.utils import clip_region

from .base import BaseScaler
from .proxy import get_proxy


def get_timeseries(
    timeseries: dict[str, scmdata.ScmRun],
    source: str,
    filters: list[dict[str, Any]],
    target_year: int,
) -> scmdata.ScmRun:
    """
    Get matching point for a given year and set of filters.

    Parameters
    ----------
    timeseries
        Set of loaded timeseries
    source
        Selected timeseries.

        Must be a valid key in ``timeseries``
    filters
        Set of filters to apply
    target_year
        Year to filter for

        This year must be in contained in the selected timeseries or be able to be
        interpolated.

    Raises
    ------
    ValueError
        No or more than one timeseries is matched

        Incorrect value for ``source``

    Returns
    -------
    Matched point after selecting and filtering. The returned ``scmdata.ScmRun`` will
    be a single values (with shape=(1, 1))
    """
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


def _check_unit(unit: str) -> None:
    parsed_unit = unit_registry(unit)

    msg = "Expected unit of the form [X] * [mass] / [time]"

    if (
        len(parsed_unit.dimensionality) != 3
        and parsed_unit.dimensionality["[mass]"] != 1
        and parsed_unit.dimensionality["[time]"] != -1
        and "[length]" not in parsed_unit.dimensionality
    ):
        raise ValueError(msg)


def apply_amount(amount: float, unit: str, proxy: xr.DataArray) -> xr.DataArray:
    """
    Distribute an amount of emissions across a proxy.

    Parameters
    ----------
    amount
        Quantity of emissions
    unit
        Unit of emissions
    proxy
        Proxy.

        Should be 2-d with dimensions of lat and lon

    Returns
    -------
        New data array using the density of the proxy. This is mass-preserving.
    """
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
    """Scale a spatial pattern using a timeseries."""

    proxy: str
    proxy_region: str
    source_timeseries: str
    source_filters: list[dict[str, Any]]

    def __call__(
        self,
        *,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        timeseries: dict[str, scmdata.ScmRun],
        target_year: int,
        **kwargs,
    ) -> xr.DataArray:
        """
        Apply scaling.

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
            Scaled DataArray
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
        """Factory method of TimeseriesScaler."""
        return TimeseriesScaler(
            proxy=method.proxy,
            proxy_region=method.proxy_region or method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters=method.source_filters,
        )
