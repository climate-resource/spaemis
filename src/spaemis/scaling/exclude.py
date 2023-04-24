import numpy as np
import xarray as xr
from attrs import define

from spaemis.config import ExcludeScaleMethod

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
        """Do not apply any scaling."""
        scaled = data.copy()

        scaled[:, :] = np.nan

        return scaled

    @classmethod
    def create_from_config(cls, method: ExcludeScaleMethod) -> "ExcludedScaler":
        """Factory method to create an ExcludedScaler."""
        return ExcludedScaler()
