"""
Loading emissions inventories
"""
import glob
import logging
import os
from typing import Any, Callable, Optional, Union

import geopandas
import pandas as pd
import xarray as xr
from attrs import Attribute, define, field

from spaemis.constants import RAW_DATA_DIR
from spaemis.utils import clip_region

logger = logging.getLogger(__name__)


def has_dimensions(
    dimensions: Union[str, list[str]]
) -> Callable[[Any, Attribute, Union[xr.Dataset, xr.DataArray]], None]:
    """
    Check if a xarray Dataset or DataArray has the expected dimensions

    Parameters
    ----------
    dimensions
        Dimensions to checks

    Raises
    ------
    ValueError
        If any of the requested dimensions are not present in the data array
    """
    dims: list[str] = [dimensions] if isinstance(dimensions, str) else dimensions

    def _check(instance, attribute, value: Union[xr.Dataset, xr.DataArray]) -> None:
        for exp_dim in dims:
            if exp_dim not in value.dims:
                raise ValueError(f"Missing dimension: {exp_dim}")

    return _check


@define
class EmissionsInventory:
    """
    An emissions inventory is a set of bottom up
    """

    data: xr.Dataset = field(
        validator=[
            has_dimensions(["lat", "lon", "sector"]),
        ]
    )
    border_mask: geopandas.GeoDataFrame
    year: int

    @classmethod
    def load_from_directory(cls, data_directory) -> "EmissionsInventory":
        """
        Load an emissions inventory from a directory
        """
        pass


class VictoriaGrid:
    """
    Information about the grid used in Victoria
    """

    nx: int = 903
    ny: int = 592
    x0: float = 140.6291
    y0: float = -39.5402
    dx: float = 0.01059988
    dy: float = 0.01059988

    @property
    def lats(self) -> list[float]:
        """
        Latitudes of the grid
        """
        return [self.y0 + self.dy * i for i in range(self.ny)]

    @property
    def lons(self) -> list[float]:
        """
        Longitudes of the grid
        """
        return [self.x0 + self.dx * i for i in range(self.nx)]


@define
class VictoriaEPAInventory(EmissionsInventory):
    """
    Victorian EPA data

    CSV files of 1D datapoints. Each grid is slightly different so some post-processing
    is required to get all the variables and sectors on to the same grid.
    """

    @classmethod
    def load_from_directory(
        cls,
        data_directory: str,
        file_suffix: str = "_tif_to_csv3.csv",
        grid: Optional[Any] = None,
    ) -> "VictoriaEPAInventory":
        """
        Load Victorian EPA inventory data

        Parameters
        ----------
        data_directory
            Folder containing CSV input files

        grid
            Object containing information about the target grid

        Returns
        -------
        Loaded data
        """
        fnames = sorted(glob.glob(os.path.join(data_directory, "*.csv")))
        if not fnames:
            raise ValueError("No inventory files found for Victoria")

        if grid is None:
            grid = VictoriaGrid()

        def read_file(fname):
            dataframe = pd.read_csv(fname).set_index(["lat", "lon"])
            dataset = xr.Dataset.from_dataframe(dataframe)
            dataset["lat_new"] = grid.lats
            dataset["lon_new"] = grid.lons

            del dataset["lat"]
            del dataset["lon"]

            return dataset.rename({"lat_new": "lat", "lon_new": "lon"}).assign_coords(
                {"sector": os.path.basename(fname).replace(file_suffix, "")}
            )

        merged_data = xr.concat([read_file(f) for f in fnames], dim="sector")
        merged_data = merged_data.where(merged_data > 0)

        vic_border = geopandas.read_file(
            os.path.join(RAW_DATA_DIR, "masks", "victoria_border_mask.gpkg")
        )
        return VictoriaEPAInventory(
            data=clip_region(merged_data, vic_border), border_mask=vic_border, year=2016
        )


def load_inventory(
    inventory: str, year: Optional[int] = None, data_directory: Optional[str] = None
) -> EmissionsInventory:
    """
    Load an emissions inventory

    Parameters
    ----------
    inventory
        Inventory name
    year
        Year of inventory to load

    data_directory
        If provided, override the default directory to load data from

    Returns
    -------
        EmissionsInventory with loaded data

    Raises
    ------
    KeyError
        Could not determine the appropriate inventory to load

    """
    data_directory = data_directory or os.path.join(
        RAW_DATA_DIR, "inventories", inventory, str(year)
    )
    mapping = {("victoria", 2016): VictoriaEPAInventory}

    try:
        loader = mapping[(inventory, year)]
    except KeyError:
        raise ValueError(f"No inventory matching {inventory}|{year}")

    return loader.load_from_directory(data_directory=data_directory)


def write_inventory_csvs(ds: xr.Dataset, output_dir: str):
    """
    Serialize a Dataset to CSV files with the same  format as the input inventory data

    Each sector is written into a different file. The CSV file contains rows of data for
    each datapoint on a lat, lon grid. Each variable will be written as a separate column.

    The ordering of the datapoints are lat-major (i.e. iterate over latitude and then
    longitude)

    Parameters
    ----------
    ds
        Data to output

        This dataset should be similar to the format from :attr:`EmissionsInventory.data`.
        in that each data variable contains a sector, lat and lon dimension.
    output_dir
        Output directory for the
    """
    sectors = ds["sector"].values

    for sector in sectors:
        sector_data = ds.sel(sector=sector)
        sector_data = sector_data.reset_coords(
            [k for k in sector_data.coords.keys() if k not in ["lat", "lon"]], drop=True
        )

        output_fname = f"{sector}_projected.csv"

        logger.info(f"Writing output file: {os.path.join(output_dir, output_fname)}")

        df = sector_data.fillna(0).to_dataframe(["lon", "lat"]).reset_index()
        # Round to be similar to the input inventory files
        df["lat"] = df["lat"].round(4)
        df["lon"] = df["lon"].round(4)

        df.to_csv(os.path.join(output_dir, output_fname), index=False)
