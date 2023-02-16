import os
from typing import Any, Dict, List

import scmdata
import xarray as xr
from attrs import define

from spaemis.config import ProxyMethod
from spaemis.constants import PROCESSED_DATA_DIR
from spaemis.input_data import _apply_filters
from spaemis.inventory import EmissionsInventory
from spaemis.unit_registry import convert_to_target_unit
from spaemis.utils import clip_region

from .base import BaseScaler


def get_proxy(proxy_name: str) -> xr.DataArray:
    root_dir = os.path.join(PROCESSED_DATA_DIR, "proxies")
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
    return xr.load_dataset(proxies[proxy_name])[proxy_name]


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

        # Adjust to kg X/yr
        scale_factor = convert_to_target_unit(
            ts.get_unique_meta("unit", True), target_unit="kg"
        )
        ts["unit"] = str(scale_factor.u)
        ts = ts * scale_factor.m

        lat = inventory.data.lat
        lon = inventory.data.lon

        proxy = get_proxy(self.proxy)
        total = proxy.sum()
        proxy_clipped = clip_region(proxy, inventory.border_mask)
        region_total = proxy_clipped.sum()

        region_share = region_total / total

        # Calculate density map
        proxy_scaled = proxy_clipped.interp(lat=lat, lon=lon)
        proxy_density = proxy_scaled / proxy_scaled.sum()

        scaled = ts.values.squeeze() * region_share * proxy_density
        scaled.attrs["units"] = ts.get_unique_meta("unit", True) + " / cell"

        return scaled

    @classmethod
    def create_from_config(cls, method: ProxyMethod) -> "ProxyScaler":
        return ProxyScaler(
            proxy=method.proxy,
            source_timeseries=method.source_timeseries,
            source_filters=method.source_filters,
        )
