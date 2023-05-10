"""
Proxy scaler

A proxy scaler uses a proxy (a 2d pattern) to disaggregate an emissions timeseries over a target area.

The proxy must cover the area of interest of the emissions timeseries
"""
import logging
from typing import Any

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import ScalerMethod, TimeseriesMethod
from spaemis.input_data import _apply_filters
from spaemis.inventory import EmissionsInventory
from spaemis.unit_registry import convert_to_target_unit, unit_registry
from spaemis.utils import clip_region

from .base import BaseScaler
from .proxy import get_proxy


def get_timeseries_point(
    timeseries: dict[str, scmdata.ScmRun],
    source: str,
    filters: list[dict[str, str]],
    target_year: int,
) -> scmdata.ScmRun:
    """
    Extract a single value according to some filters

    Parameters
    ----------
    timeseries
        Collection of loaded timeseries
    source
        Timeseries name
    filters
        Filter to apply to the selected timeseries

        These filters if applied must result in a single remaining timeseries otherwise
        a ``ValueError`` will be raised.
    target_year
        Year to extract

        Must be contained in the targeted timeseries

    Raises
    ------
    ValueError
        If the selected data cannot be retrieved

    Returns
    -------
        ScmRun with a containing a single timeseries and year.

        This object will retain the metadata of the filtered timeseries
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
    pint_unit = unit_registry(unit)

    msg = "Expected unit of the form [X] * [mass] / [time]"

    if (
        len(pint_unit.dimensionality) != 3  # noqa
        and pint_unit.dimensionality["[mass]"] != 1
        and pint_unit.dimensionality["[time]"] != -1
        and "[length]" not in pint_unit.dimensionality
    ):
        raise ValueError(msg)


def apply_amount(amount: float, unit: str, proxy: xr.DataArray) -> xr.DataArray:
    """
    Scale a known amount of emissions across a proxy

    Parameters
    ----------
    amount
        Amount of stuff to allocate across the proxy

        The stuff is usually annual emissions of a given species and currently
    unit
        Unit of the stuff

        Must be able to be converted to a Pint unit with dimensions [X] * [mass] / [time]
        where X can be any dimension (typically CO2 or other species in the case of emissions)
    proxy
        Proxy array

        Can include nans and missing data

    Returns
    -------
        DataArray with the same dimensions of ``proxy`` where the sum matches ``amount``
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
    """
    Scale a spatial pattern using a timeseries
    """

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
        **kwargs: Any,
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
            Scaled data
        """
        ts = get_timeseries_point(
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
    def create_from_config(cls, method: ScalerMethod) -> "TimeseriesScaler":
        """
        Create Scaler from configuration
        """
        if not isinstance(method, TimeseriesMethod):
            raise TypeError("Incompatible configuration")

        return TimeseriesScaler(
            proxy=method.proxy,
            proxy_region=method.proxy_region or method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters=method.source_filters,
        )
