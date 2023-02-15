import os
from typing import Any, Dict, List

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import ProxyMethod
from spaemis.constants import PROCESSED_DATA_DIR
from spaemis.input_data import _apply_filters
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region

from .base import BaseScaler


def get_proxy(proxy_name: str) -> xr.DataArray:
    root_dir = os.path.join(PROCESSED_DATA_DIR, "proxies")
    proxies = {
        "Population": os.path.join(
            root_dir,
            "sedacs",
            "gpw_v4_population_density_adjusted_to_2015_unwpp_country_totals_rev11_2020_2pt5_aus.nc",
        )
    }
    return xr.load_dataarray(proxies[proxy_name])


def _get_timeseries(timeseries, source, filters, target_year) -> scmdata.ScmRun:
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


@define
class ProxyScaler(BaseScaler):
    """
    Use a proxy to distribute a set quantity spatially
    """

    proxy: str
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
        ts = _get_timeseries(
            timeseries,
            self.source_timeseries,
            self.source_filters,
            target_year=target_year,
        )

        lat = inventory.data.lat
        lon = inventory.data.lon

        proxy = get_proxy(self.proxy)
        total = proxy.sum()
        proxy_clipped = clip_region(proxy, inventory.border_mask)
        region_total = proxy_clipped.sum()

        region_share = region_total / total

        # Calculate density o
        proxy_scaled = proxy.interp(lat=lat, lon=lon)
        proxy_density = proxy_scaled / proxy_scaled.sum()

        scaled = ts.values.squeeze() * region_share * proxy_density

        return scaled

    @classmethod
    def create_from_config(cls, method: ProxyMethod) -> "ProxyScaler":
        return ProxyScaler(
            proxy=method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters={},
        )
