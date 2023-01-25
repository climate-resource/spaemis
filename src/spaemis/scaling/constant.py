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

    def __call__(self, data: xr.DataArray, **kwargs) -> xr.DataArray:
        return data * self.scaling_factor

    @classmethod
    def create_from_method(cls, method: ConstantScaleMethod) -> "ConstantScaler":
        return ConstantScaler(method.scale_factor)
