import logging

import xarray as xr
from attrs import define

from spaemis.config import RelativeChangeMethod
from spaemis.input_data import SECTOR_MAP, database
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region, weighted_annual_mean

from .base import BaseScaler

logger = logging.getLogger(__name__)


def _covers(dataarray: xr.DataArray, dim: str, value: float) -> bool:
    """
    Check if a dimension of a DataArray can be interpolated for a given value

    If this check fails an extrapolation will be required
    Parameters
    ----------
    dataarray
        DataArray to check
    dim
        Dimension of interest
    value
        Value to check

    Returns
    -------
    True if `value` could be interpolated in `DataArray`'s dimension `dim`
    """
    return bool(dataarray[dim].min() <= value <= dataarray[dim].max())


@define
class RelativeChangeScaler(BaseScaler):
    """
    Apply the relative change from one timeseries

    Uses input4MIPs data to perform the scaling
    """

    variable_id: str
    source_id: str
    sector_id: int

    def load_source(self, inventory, weighted_temporal_mean=False) -> xr.DataArray:
        """
        Load and preprocess the appropriate input4MIPs data


        Parameters
        ----------
        inventory
        weighted_temporal_mean
            IF True, temporally weight the annual mean to capture the varying number
            of days in each month

        Returns
        -------
            Annual mean values over the same domain as the inventory data
        """
        dataset = database.load(source_id=self.source_id, variable_id=self.variable_id)
        dataset = dataset.sel(sector=self.sector_id)

        # The input4MIPS emissions are all in kg/m2/s so we take means rather than sums
        variable_name = self.variable_id.replace("-", "_")
        if weighted_temporal_mean:
            annual_mean = weighted_annual_mean(dataset, variable_name)
        else:
            annual_mean = dataset[variable_name].groupby("time.year").mean()

        clipped = clip_region(annual_mean, inventory.border_mask)
        return clipped

    def __call__(
        self,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        target_year: int,
    ) -> xr.DataArray:
        source = self.load_source(inventory)
        if tuple(sorted(source.dims)) != ("lat", "lon", "year"):
            raise AssertionError(
                f"Excepted only lat, lon and year dims. Got: {source.dims}"
            )

        if not _covers(source, "year", inventory.year):
            logger.warning(
                f"source {source.name} does not cover inventory year. Extrapolating"
            )
        if not _covers(source, "year", target_year):
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

        return scaled

    @classmethod
    def create_from_config(cls, method: RelativeChangeMethod) -> "RelativeChangeScaler":
        try:
            sector_id = SECTOR_MAP.index(method.sector)
        except ValueError as exc:
            raise ValueError(f"Unknown input4MIPs sector: {method.sector}") from exc

        return RelativeChangeScaler(
            source_id=method.source_id,
            variable_id=method.variable_id,
            sector_id=sector_id,
        )