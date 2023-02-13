import xarray as xr
from attrs import define

from spaemis.config import ConstantScaleMethod

from .base import BaseScaler


@define
class ConstantScaler(BaseScaler):
    """
    Apply some constant scale factor to an inventory
    """

    scaling_factor: float

    def __call__(self, data: xr.DataArray, target_year: int, **kwargs) -> xr.DataArray:
        scaled = data * self.scaling_factor

        return scaled

    @classmethod
    def create_from_config(cls, method: ConstantScaleMethod) -> "ConstantScaler":
        return ConstantScaler(method.scale_factor)
