"""
Scale using the relative change seen in input4MIPs
"""

import logging
from typing import Any

import xarray as xr
from attrs import define

from spaemis.config import RelativeChangeMethod, ScalerMethod
from spaemis.input_data import SECTOR_MAP
from spaemis.inventory import EmissionsInventory
from spaemis.utils import covers

from .base import BaseScaler, load_source

logger = logging.getLogger(__name__)


@define
class RelativeChangeScaler(BaseScaler):
    """
    Apply the relative change from one timeseries

    Uses input4MIPs data to perform the scaling
    """

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
        Run a scaler

        Parameters
        ----------
        data
            Data to scale
        inventory
            Emissions inventory
        target_year
            Year to scale to

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

        if not covers(source, "year", inventory.year):
            logger.warning(
                f"source {source.name} does not cover inventory year. Extrapolating"
            )
        if not covers(source, "year", target_year):
            logger.warning(
                f"source {source.name} does not cover target year. Extrapolating"
            )

        # Get the target and inventory year data (extrapolating if necessary)
        inv_year_map = source.interp(
            year=inventory.year,
            kwargs={"fill_value": "extrapolate"},
        )
        target_year_map = source.interp(
            year=target_year,
            kwargs={"fill_value": "extrapolate"},
        )

        scale_factor = (target_year_map - inv_year_map) / inv_year_map

        # Regrid using linear interpolation
        scale_factor = scale_factor.interp(lat=data.lat, lon=data.lon)

        scaled = data * (1 + scale_factor)
        scaled.attrs.update(data.attrs)

        return scaled

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "RelativeChangeScaler":
        """
        Create a scaler from configuration
        """
        if not isinstance(method, RelativeChangeMethod):
            raise TypeError("Incompatible configuration")

        if method.sector not in SECTOR_MAP:
            raise ValueError(f"Unknown input4MIPs sector: {method.sector}")

        return RelativeChangeScaler(
            source_id=method.source_id,
            variable_id=method.variable_id,
            sector=method.sector,
        )
