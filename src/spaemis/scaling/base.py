import xarray as xr

from spaemis.config import ScalerMethod
from spaemis.inventory import EmissionsInventory


class BaseScaler:
    """
    Scaling calculator

    Used to modify a dataset using a scaling method
    """

    def __call__(
        self,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        target_year: int,
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
        raise NotImplementedError

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "BaseScaler":
        """
        Factory for creating a new scaler

        Parameters
        ----------
        method
            Configuration to create the scaler

        Returns
        -------
            New scaler instance configured according to the configuration
        """
        raise NotImplementedError
