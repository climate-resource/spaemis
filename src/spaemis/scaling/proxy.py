"""
Proxy scaler

A proxy scaler uses a proxy (a 2d pattern) to disaggregate an emissions timeseries over a target area.

The proxy must cover the area of interest of the emissions timeseries
"""
import logging
import os
from typing import Any

import numpy as np
import numpy.testing as npt
import xarray as xr
from attrs import define

from spaemis.config import ProxyMethod, ScalerMethod
from spaemis.constants import PROCESSED_DATA_DIR
from spaemis.input_data import SECTOR_MAP
from spaemis.inventory import EmissionsInventory, load_inventory
from spaemis.utils import area_grid, clip_region, covers

from .base import BaseScaler, load_source

logger = logging.getLogger(__name__)


def get_proxy(proxy_name: str, inventory: EmissionsInventory) -> xr.DataArray:
    """
    Retrieve a proxy given a name

    The prefix of the proxy species the type of proxy used. The options for proxies
    are:

    * population - Spatial population from SEDACS
    * residential_density - Map of residential density over Australia
    * inventory|X - Data for a sector X from the current inventory. The NOx variable is used
    * australian_inventory|X - Data for a sector X from the Australian inventory. The NOx
        variable is used

    For the population and residential_density proxies, a precalculated file is used. The
    scripts for generating these files are in `scripts/`. By default, the location for
    these proxies is `data/processed/proxies`, but this can be overridden using the
    `SPAEMIS_PROXY_DIRECTORY` environment variable.

    Parameters
    ----------
    proxy_name
        Name of proxy

        Can include a "|" to denote hierarchy
    inventory
        An emission inventory in the case the "inventory" proxy is used

    Returns
    -------
        Selected proxy field with dimensions lat and lon

        The latitude/longitude grid of the proxy may differ depending on the choice
    """
    root_dir = os.environ.get(
        "SPAEMIS_PROXY_DIRECTORY", os.path.join(PROCESSED_DATA_DIR, "proxies")
    )

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

    raise ValueError("Unknown proxy")


@define
class ProxyScaler(BaseScaler):
    """
    Combine global emissions with a proxy

    The spatial pattern of the global emissions are ignored, but the quantity over the area of interest is
    preserved.
    """

    proxy: str
    variable_id: str
    source_id: str
    sector: str

    def __call__(
        self,
        *,
        data: xr.DataArray,
        inventory: EmissionsInventory,
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
        source = load_source(
            self.source_id,
            self.variable_id,
            self.sector,
            inventory,
        )
        if tuple(sorted(source.dims)) != ("lat", "lon", "year"):  # type: ignore
            raise AssertionError(
                f"Excepted only lat, lon and year dims. Got: {source.dims}"
            )

        if not covers(source, "year", target_year):
            logger.warning(
                f"source {source.name} does not cover target year. Extrapolating"
            )

        if source.attrs["units"] != "kg m-2 s-1":
            raise AssertionError(f"Unexpected units: {source.attrs['units']}")
        areas = area_grid(source.lat, source.lon)
        source_emissions = source.interp(year=target_year) * areas * 365 * 24 * 60 * 60
        source_emissions.attrs["units"] = "kg / cell / yr"

        total_emms = source_emissions.sum().values.squeeze()

        lat = data.lat
        lon = data.lon

        # Calculate density map over the area of interest
        # proxy grid is interpolated onto the target grid before clipping
        proxy = get_proxy(self.proxy, inventory=inventory)

        proxy_interp = clip_region(
            proxy.interp(lat=lat, lon=lon), inventory.border_mask
        ).interp(lat=lat, lon=lon)
        proxy_density = proxy_interp / proxy_interp.sum()
        npt.assert_allclose(proxy_density.sum().values, np.asarray(1))

        scaled: xr.DataArray = total_emms * proxy_density  # type: ignore
        scaled.attrs["units"] = "kg / cell / yr"

        return scaled

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "ProxyScaler":
        """
        Create a scaler from configuration
        """
        if not isinstance(method, ProxyMethod):
            raise TypeError("Incompatible configuration")
        if method.sector not in SECTOR_MAP:
            raise ValueError(f"Unknown input4MIPs sector: {method.sector}")

        return ProxyScaler(
            proxy=method.proxy,
            variable_id=method.variable_id,
            source_id=method.source_id,
            sector=method.sector,
        )
