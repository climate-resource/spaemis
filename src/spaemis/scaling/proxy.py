from typing import Any, Dict

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import ProxyMethod
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region

from .base import BaseScaler


def get_proxy(proxy_name: str) -> xr.DataArray:
    pass


def _get_timeseries(timeseries, source, filters, target_year) -> scmdata.ScmRun:
    try:
        ts = timeseries[source]
    except KeyError as exc:
        raise KeyError(f"Source dataset is not loaded: {source}") from exc

    # This linearly interpolates the timeseries
    ts = ts.filter(**filters).resample("AS")

    if len(ts) == 0:
        raise ValueError(f"No data matching {filters} was found in {source} input data")

    if len(ts) > 1:
        raise ValueError(
            f"More than one match was found for {filters} in {source} input data"
        )

    if target_year not in ts["year"]:
        raise ValueError(f"No timeseries data for year={target_year} available")

    ts = ts.filter(year=target_year)

    if ts.shape != (1, 1):
        raise AssertionError("Something went wrong when filtering timeseries")
    return ts


@define
class ProxyScaler(BaseScaler):
    """
    Use a proxy to distribute a set quantity spatially
    """

    proxy: str
    source_timeseries: str
    source_filters: Dict[str, Any]

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
        ts = _get_timeseries(
            timeseries,
            self.source_timeseries,
            self.source_filters,
            target_year=target_year,
        )

        lat = inventory.data.lat
        lon = inventory.data.lon

        proxy = clip_region(get_proxy(self.proxy), inventory.border_mask)
        proxy_scaled = proxy.interp(lat=lat, lon=lon)

        scaled = ts.values.squeeze() * proxy_scaled

        return scaled

    @classmethod
    def create_from_config(cls, method: ProxyMethod) -> "ProxyScaler":
        return ProxyScaler(
            proxy=method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters={},
        )