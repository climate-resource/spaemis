import numpy as np
import xarray as xr
from attrs import define

from spaemis.config import ConstantScaleMethod

from .base import BaseScaler


@define
class ExcludedScaler(BaseScaler):
    """
    Don't apply any scaling.

    All results will be nan
    """

    def __call__(
        self, *, data: xr.DataArray, target_year: int, **kwargs
    ) -> xr.DataArray:
        scaled = data.copy()

        scaled[:, :] = np.nan

        return scaled

    @classmethod
    def create_from_config(cls, method) -> "ConstantScaler":
        return ExcludedScaler()
