"""
Constant scaler

Apply a constant scale factor to the base inventory
"""
from typing import Any

import xarray as xr
from attrs import define

from spaemis.config import ConstantScaleMethod, ScalerMethod

from .base import BaseScaler


@define
class ConstantScaler(BaseScaler):
    """
    Apply some constant scale factor to an inventory
    """

    scaling_factor: float

    def __call__(
        self, *, data: xr.DataArray, target_year: int, **kwargs: Any
    ) -> xr.DataArray:
        """
        Run a scaler

        Parameters
        ----------
        data
            Data to scale
        target_year
            Year to scale to

        Returns
        -------
            Scaled data
        """
        scaled = data * self.scaling_factor

        return scaled

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "ConstantScaler":
        """
        Create a new scaler from configuration

        Parameters
        ----------
        method
            Configuration to create the scaler

        Returns
        -------
            New scaler instance configured according to the configuration
        """
        if not isinstance(method, ConstantScaleMethod):
            raise TypeError("Incompatible configuration")

        return ConstantScaler(method.scale_factor)
