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
        # TODO figure out call format
        raise NotImplementedError

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "BaseScaler":
        raise NotImplementedError
