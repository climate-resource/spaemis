import xarray as xr
from attrs import define

from spaemis.config import RelativeChangeMethod
from spaemis.input_data import database
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region, weighted_annual_mean

from .base import BaseScaler


@define
class RelativeChangeScaler(BaseScaler):
    """
    Apply the relative change from one timeseries

    Take a
    """

    variable_id: str
    source_id: str

    def load_source(self, inventory, weighed_temporal_mean=False) -> xr.DataArray:
        # These emissions are all in kg/m2/s so we take means rather than sums
        ds = database.load(source_id=self.source_id, variable_id=self.variable_id)

        variable_name = self.variable_id.replace("-", "_")
        if weighed_temporal_mean:
            annual_mean = weighted_annual_mean(ds, variable_name)
        else:
            annual_mean = ds[variable_name].groupby("time.year").mean()

        clipped = clip_region(annual_mean, inventory.border_mask)
        return clipped

    def __call__(
        self,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        target_year: int,
    ) -> xr.DataArray:
        source = self.load_source(inventory)

        inv_map = source.sel(time=str(inventory.year))
        target_map = source.sel(time=str(inventory.year))
        scale_factor = target_map - inv_map / inv_map  # TODO: check op

        # Regrid?

        return data * scale_factor

    @classmethod
    def create_from_config(cls, method: RelativeChangeMethod) -> "RelativeChangeScaler":
        return RelativeChangeScaler(source_id=method.source, variable_id=method.source)
