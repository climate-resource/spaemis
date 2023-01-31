import xarray as xr
from attrs import define

from spaemis.config import ConstantScaleMethod

from .base import BaseScaler


@define
class RelativeChangeScaler(BaseScaler):
    """
    Apply the relative change from one timeseries

    Take a
    """

    def load_source(self) -> xr.DataArray:
        return

    def __call__(self, data: xr.DataArray, **kwargs) -> xr.DataArray:
        return data * self.scaling_factor

    @classmethod
    def create_from_config(cls, method: ConstantScaleMethod) -> "RelativeChangeScaler":
        return RelativeChangeScaler()
