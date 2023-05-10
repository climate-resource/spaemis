"""
Exclude scaler
"""

from typing import Any

import numpy as np
import xarray as xr
from attrs import define

from spaemis.config import ScalerMethod

from .base import BaseScaler


@define
class ExcludedScaler(BaseScaler):
    """
    Don't apply any scaling.

    All results will be nan
    """

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
        scaled = data.copy()

        scaled[:, :] = np.nan

        return scaled

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "ExcludedScaler":
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
        return ExcludedScaler()
