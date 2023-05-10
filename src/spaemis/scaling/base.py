"""
Base class for scaling emissions
"""

import scmdata
import xarray as xr

from spaemis.config import ScalerMethod
from spaemis.input_data import SECTOR_MAP, database
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region, weighted_annual_mean


def load_source(
    source_id: str,
    variable_id: str,
    sector: str,
    inventory: EmissionsInventory,
    weighted_temporal_mean: bool = False,
) -> xr.DataArray:
    """
    Load and preprocess the appropriate input4MIPs data

    Parameters
    ----------
    source_id
        Source of the dataset to load
    variable_id
        Variable identifier of the dataset to load
    sector
        Sector to load.
        Must be in :attr:`SECTOR_MAP`
    inventory
    weighted_temporal_mean
        IF True, temporally weight the annual mean to capture the varying number
        of days in each month

    Returns
    -------
        Annual mean values over the same domain as the inventory data
    """
    dataset = database.load(source_id=source_id, variable_id=variable_id)
    dataset = dataset.sel(sector=SECTOR_MAP.index(sector))

    # The input4MIPS emissions are all in kg/m2/s so we take means rather than sums
    variable_name = variable_id.replace("-", "_")
    if weighted_temporal_mean:
        annual_mean = weighted_annual_mean(dataset, variable_name)
    else:
        annual_mean = dataset[variable_name].groupby("time.year").mean()

    clipped = clip_region(annual_mean, inventory.border_mask)
    return clipped


class BaseScaler:
    """
    Scaling calculator

    Used to modify a dataset using a scaling method
    """

    def __call__(
        self,
        *,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        target_year: int,
        timeseries: dict[str, scmdata.ScmRun],
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
        timeseries
            Additional timeseries for use by the scaler if needed

        Returns
        -------
            Scaled data
        """
        raise NotImplementedError

    @classmethod
    def create_from_config(cls, method: ScalerMethod) -> "BaseScaler":
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
        raise NotImplementedError
